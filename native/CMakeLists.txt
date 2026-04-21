cmake_minimum_required(VERSION 3.20)
project(coyin_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(coyin_native SHARED
    src/coyin_native.cpp
)

target_include_directories(coyin_native PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

if (MSVC)
    target_compile_options(coyin_native PRIVATE /utf-8)
endif()

set_target_properties(coyin_native PROPERTIES
    OUTPUT_NAME "coyin_native"
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)
