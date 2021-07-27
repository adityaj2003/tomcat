#include <string>
#include <vector> 
#include <filesystem>
#include <iostream>
#include "MetadataPreprocessor.h"

using namespace std;
MetadataPreprocessor::MetadataPreprocessor(string trial_path){
	this->trial_path = trial_path;

	 // Remove _modified files
        string command = "rm " + trial_path + "/*_modified";
        system(command.c_str());	

	this->get_metadata_data();
	this->remove_asr_messages();
}

MetadataPreprocessor::~MetadataPreprocessor(){

}

void MetadataPreprocessor::get_metadata_data(){
	for (const auto & entry : filesystem::directory_iterator(this->trial_path)){
                std::string filename = entry.path();

                // Check file extension
                size_t i = filename.rfind(".metadata", filename.length());
                if(i != string::npos){
                        // Push back filename
                        this->metadata_filename = filename;

                }
        }
}

void MetadataPreprocessor::remove_asr_messages(){
        string pattern1 = "!/\"topic\": \"metadata\\/audio\"/";
	string pattern2 = "!/\"topic\": \"agent\\/asr\\/intermediate\"/";
	string pattern3 = "!/\"topic\": \"agent\\/asr\\/final\"/";
	string pattern4 = "!/\"topic\": \"agent\\/dialog\"/";
	string command =  "awk '" + pattern1  + " && " +  pattern2 + " && " + pattern3 + " && " + pattern4 + "' " + this->metadata_filename + " > " + this->metadata_filename + "_modified";
	system(command.c_str());	
}

