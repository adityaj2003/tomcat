project(replayer)

cmake_minimum_required(VERSION 3.15)

set(CMAKE_CXX_STANDARD 17)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
add_definitions(-DBOOST_LOG_DYN_LINK)
find_package(Boost COMPONENTS program_options REQUIRED)
find_package(nlohmann_json REQUIRED)

add_executable(replayer src/WebsocketClient.cpp src/AudioChunkPreprocessor.cpp)

target_link_libraries(replayer nlohmann_json::nlohmann_json ${Boost_LIBRARIES} -pthread)

file(COPY audio/ DESTINATION ${CMAKE_CURRENT_BINARY_DIR}/audio/)
