#include <cstdlib>
#include <vector>
#include <string>
#include <iostream>
#include <filesystem>
#include <fstream>
#include <regex>
#include "AudioChunkPreprocessor.h"
using namespace std;

AudioChunkPreprocessor::AudioChunkPreprocessor(string trial_path){
	this->trial_path = trial_path;

	// Remove _raw files
	string command = "rm " + trial_path + "/*_raw"; 
	system(command.c_str());
	
	// Process audio chunks
	this->get_audio_file_data();
	this->convert_audio_files();
	this->create_audio_chunks();
}

AudioChunkPreprocessor::~AudioChunkPreprocessor(){

}      

// Get audio filenames and participant ids from Trial directory
void AudioChunkPreprocessor::get_audio_file_data(){	
	for (const auto & entry : filesystem::directory_iterator(this->trial_path)){
		std::string filename = entry.path();
			
		// Check file extension
		size_t i = filename.rfind(".wav", filename.length());
		if(i != string::npos){
			// Push back filename
			this->audio_filenames.push_back(filename);

			// Push back participant id
			regex rgx(".*Member-(.*?)_.*");
			smatch matches;
			regex_search(filename, matches, rgx);
			this->participant_ids.push_back(matches[1].str());

			// Push back sample rate
			FILE *file;
			file = fopen(filename.c_str(), "rb");
			char a[4];
			fseek(file,  24, SEEK_SET); // The sample rate if stored at bytes 24-27
			for(int i=0;i<4;i++){
				a[i] = fgetc(file);	
			}
			fclose(file);
			this->sample_rates.push_back(*((int*)a));
			
		}
	}
}


// Convert .wav files to raw pcm files
void AudioChunkPreprocessor::convert_audio_files(){
	// Convert files
	for(int i=0; i<audio_filenames.size();i++){
		std::cout << audio_filenames[i] << std::endl;
		string command = "ffmpeg -i " + audio_filenames[i] + " -f s16le -acodec pcm_s16le " + audio_filenames[i] + "_raw";
		system(command.c_str());
	}
}


void AudioChunkPreprocessor::create_audio_chunks(){
	for (int i=0;i<audio_filenames.size(); i++){
		this->num_participants++;
		
		// Create a new vector for storing chunks
		vector<vector<int16_t>> chunks;

		// Open audio file
		string converted_path = audio_filenames[i] + "_raw";
	 	FILE *audio_file = fopen(converted_path.c_str(), "rb");

		// Read from audio file
		std::vector<int16_t> chunk(4096);
		int length=-1;
		while(length = fread(&chunk[0], sizeof(int16_t), 4096, audio_file) != 0){
			// Push back chunk
			chunks.push_back(chunk);	
		}

		// Close audio file
		fclose(audio_file);

		// Add participant chunks to AudioChunkPreprocessor
		this->audio_chunks.push_back(chunks);
	}	
}


