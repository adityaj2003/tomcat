class MetadataPreprocessor{
	public:
		MetadataPreprocessor(std::string trial_path);
		~MetadataPreprocessor();

		std::string trial_path;
		std::string metadata_filename;
		int start_offset;
	private:
		void get_metadata_data();
		void remove_asr_messages();
};
