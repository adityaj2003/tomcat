#include <vector>
#include <string>
#include <iostream>
#include <filesystem>
#include <fstream>

#include "AudioChunkPreprocessor.h"
using namespace std;

AudioChunkPreprocessor::AudioChunkPreprocessor(string participant_audio_path){
	this->participant_audio_path = participant_audio_path;
	this->create_audio_chunks();
}

AudioChunkPreprocessor::~AudioChunkPreprocessor(){

}      


void AudioChunkPreprocessor::create_audio_chunks(){
	for (const auto & entry : filesystem::directory_iterator(this->participant_audio_path)){
		this->num_participants++;
		
		// Create a new vector for storing chunks
		vector<vector<int16_t>> chunks;

		// Open audio file
	 	FILE *audio_file = fopen(entry.path().c_str(), "rb");

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


