cmake_minimum_required(VERSION 3.10)
project(token_similarity C)

set(CMAKE_C_STANDARD 99)

add_library(token_similarity SHARED token_similarity.c)
target_include_directories(token_similarity PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(token_similarity PROPERTIES OUTPUT_NAME "token_similarity")
