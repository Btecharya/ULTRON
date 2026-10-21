cmake_minimum_required(VERSION 3.20)
project(ultron_native LANGUAGES CXX)
add_library(ultron_native SHARED ultron_native.cpp)
target_compile_features(ultron_native PRIVATE cxx_std_17)
