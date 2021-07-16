#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>
#include <chrono>

#include "AudioChunkPreprocessor.h"

namespace beast = boost::beast;         // from <boost/beast.hpp>
namespace http = beast::http;           // from <boost/beast/http.hpp>
namespace websocket = beast::websocket; // from <boost/beast/websocket.hpp>
namespace net = boost::asio;            // from <boost/asio.hpp>
using tcp = boost::asio::ip::tcp;       // from <boost/asio/ip/tcp.hpp>

using namespace std;
void run_session(vector<vector<int16_t>>, string);

int main(int argc, char** argv)
{
    // Preprocess audio chunks
    AudioChunkPreprocessor acp("./audio");

    // Create thread array
    vector<thread> thread_list;
    
    // Initilize threads 
    for(int i=0; i<acp.num_participants;i++){
	thread_list.push_back(thread(run_session, acp.audio_chunks[i], acp.participant_ids[i]));
    } 

    // Join threads 
    for(int i=0; i<acp.num_participants;i++){
	thread_list[i].join();
    } 

    
    return EXIT_SUCCESS;
}

void run_session(std::vector<std::vector<int16_t>> audio_chunks, std::string participant_id){
	int sample_rate = 48000;
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
			    std::string(BOOST_BEAST_VERSION_STRING) +
				" websocket-client-coro");
		    }));

		// Perform the websocket handshake
		ws.handshake("localhost", "/?sampleRate=48000&id=test");
		
		// Send the message
		auto start = std::chrono::high_resolution_clock::now();
		for(int i=0;i<audio_chunks.size();i++){
			ws.binary(true);
			ws.write(net::buffer(audio_chunks[i]));
		
			if(i != audio_chunks.size()-1){	
				// Sleep
				auto a = chrono::high_resolution_clock::now();
				while ((chrono::high_resolution_clock::now() -a) < chrono::duration<double>(seconds_interval) ) continue;
			}
		}
		auto stop = std::chrono::high_resolution_clock::now();
		auto duration = std::chrono::duration_cast<std::chrono::microseconds>(stop-start);
		
		std::cout << duration.count() << std::endl;
		// Close the WebSocket connection
		ws.close(websocket::close_code::normal);

		// If we get here then the connection is closed gracefully
        }
	catch(std::exception const& e){
 		std::cerr << "Error: " << e.what() << std::endl;
	}
}
