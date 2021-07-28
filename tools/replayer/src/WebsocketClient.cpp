#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>
#include <chrono>

#include <boost/program_options.hpp>

#include "AudioChunkPreprocessor.h"
#include "MetadataPreprocessor.h"
#include "Mosquitto.h"

namespace beast = boost::beast;         // from <boost/beast.hpp>
namespace http = beast::http;           // from <boost/beast/http.hpp>
namespace websocket = beast::websocket; // from <boost/beast/websocket.hpp>
namespace net = boost::asio;            // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;       // from <boost/asio/ip/tcp.hpp>

using namespace boost::program_options;
using namespace std;
void run_session(vector<vector<int16_t>>, string, int);

int main(int argc, char** argv)
{
    // Command line arguments
    string trial_directory;
    string mqtt_host;
    int mqtt_port;

     try {
        options_description desc{"Options"};
        desc.add_options()("help,h", "Help screen")(
            "trial_directory",
	    value<string>(&trial_directory)->default_value("NA"),
	    "The directory for the trial to be replayed")(
	    "mqtt_host",
            value<string>(&mqtt_host)->default_value("localhost"),
            "The host address of the mqtt broker")(
            "mqtt_port",
            value<int>(&mqtt_port)->default_value(1883),
            "The port of the mqtt broker");

        variables_map vm;
        store(parse_command_line(argc, argv, desc), vm);
        notify(vm);
    }
    catch (const error& ex) {
        cout << "Error parsing arguments" << endl;
        return -1;
    }

    // Preprocess audio chunks
    AudioChunkPreprocessor acp(trial_directory);

    // Preprocess metadata files
    MetadataPreprocessor mdp(trial_directory);
 
    // Create thread array
    vector<thread> thread_list;
    
    // Initialize mosquitto 
    MosquittoListener mqtt_client;
    mqtt_client.connect(mqtt_host, mqtt_port, 1000, 1000, 1000);
    mqtt_client.subscribe("#");
    mqtt_client.set_max_seconds_without_messages(2147483647); // Max Long value
    thread mqtt_thread = thread([&] { mqtt_client.loop(); });
    mqtt_client.start_local = chrono::system_clock::now();

    // Kill existing playback processes 
    system("killall python");

    // Start metadata playback
    thread playback_thread = thread([&] {
	    string command = "python tools/Playback.py " + mdp.metadata_filename + "_modified"; 
	    system(command.c_str());
	    cout << "replay complete" << endl;
    });

    // Initilize threads 
    for(int i=0; i<acp.num_participants;i++){
	thread_list.push_back(thread(run_session, acp.audio_chunks[i], acp.participant_ids[i], acp.sample_rates[i]));
    } 

    // Join threads 
    for(int i=0; i<acp.num_participants;i++){
	thread_list[i].join();
    } 

    mqtt_client.close();
    mqtt_thread.join();

    playback_thread.join();    
    return EXIT_SUCCESS;
}

void run_session(vector<vector<int16_t>> audio_chunks, string participant_id, int sample_rate){
	int chunk_size = 4096;
	double chunks_per_second = (double)sample_rate/(double)chunk_size;
	double seconds_interval = 1.0/(double)chunks_per_second;
	try{
		// The io_context is required for all I/O
		net::io_context ioc;

		// These objects perform our I/O
		tcp::resolver resolver{ioc};
		websocket::stream<tcp::socket> ws{ioc};

		// Look up the domain name
		auto const results = resolver.resolve("localhost", "8888");

		// Make the connection on the IP address we get from a lookup
		net::connect(ws.next_layer(), results.begin(), results.end());

		// Set a decorator to change the User-Agent of the handshake
		ws.set_option(websocket::stream_base::decorator(
		    [](websocket::request_type& req)
		    {
			req.set(http::field::user_agent,
			    string(BOOST_BEAST_VERSION_STRING) +
				" websocket-client-coro");
		    }));

		// Perform the websocket handshake
		ws.handshake("0.0.0.0", "/?sampleRate=" + to_string(sample_rate) + "&id=" + participant_id);
		
		// Send the message
		auto start = chrono::high_resolution_clock::now();
		for(int i=0;i<audio_chunks.size();i++){
			auto start_write = chrono::high_resolution_clock::now();
			ws.binary(true);
			ws.write(net::buffer(audio_chunks[i]));
			auto stop_write = chrono::high_resolution_clock::now();
			auto write_overhead = chrono::duration_cast<chrono::seconds>(stop_write-start_write);
		 	
			if(i != audio_chunks.size()-1){	
				// Sleep
				auto a = chrono::high_resolution_clock::now();
				while ((chrono::high_resolution_clock::now() -a) < chrono::duration<double>(seconds_interval-write_overhead.count()) ) continue;
			}
		}
		auto stop = chrono::high_resolution_clock::now();
		auto duration = chrono::duration_cast<std::chrono::microseconds>(stop-start);
		
		// Close the WebSocket connection
		ws.close(websocket::close_code::normal);

		// If we get here then the connection is closed gracefully
        }
	catch(std::exception const& e){
 		cerr << "Error: " << e.what() << endl;
	}
}
