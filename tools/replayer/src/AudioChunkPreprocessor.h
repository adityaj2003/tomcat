#include <vector>
#include <string>

class AudioChunkPreprocessor{
	public:
		int num_participants = 0;
		std::vector<std::vector<std::vector<int16_t>>> audio_chunks;
	
		std::string trial_path;
		std::vector<std::string> audio_filenames;
		std::vector<std::string> participant_ids;
		
		AudioChunkPreprocessor(std::string trial_path);
		~AudioChunkPreprocessor();	

		
	       	
	private:
		void get_audio_file_data();
		void convert_audio_files();
		void create_audio_chunks();
};
