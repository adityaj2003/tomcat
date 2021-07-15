#include <vector>
#include <string>

class AudioChunkPreprocessor{
	public:
		int num_participants;
		std::vector<std::vector<std::vector<int16_t>>> audio_chunks;
		std::vector<std::string> participant_ids;
		std::string participant_audio_path;
		
		AudioChunkPreprocessor(std::string participant_audio_path);
		~AudioChunkPreprocessor();	

		
	       	
	private:
		void create_audio_chunks();
};
