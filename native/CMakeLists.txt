cmake_minimum_required(VERSION 3.20)
project(coyin_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(COYIN_NATIVE_WITH_QT "Link the native module against Qt 6." ON)

if (COYIN_NATIVE_WITH_QT)
    set(CMAKE_AUTOMOC ON)
    set(CMAKE_AUTORCC ON)
    set(CMAKE_AUTOUIC ON)

    find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2 ShaderTools)
endif()

add_library(coyin_native SHARED
    include/chrome_effects_native.h
    src/coyin_native.cpp
    src/chrome_effects_native.cpp
)

target_include_directories(coyin_native PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

if (COYIN_NATIVE_WITH_QT)
    qt_add_shaders(coyin_native "coyin_visual_shaders"
        PREFIX
            "/coyin/chrome"
        FILES
            shaders/surface.vert
            shaders/signal_accent.frag
            shaders/shimmer_rail.frag
    )

    target_link_libraries(coyin_native PRIVATE
        Qt6::Core
        Qt6::Gui
        Qt6::Qml
        Qt6::Quick
        Qt6::QuickControls2
        Qt6::ShaderTools
    )
    target_compile_definitions(coyin_native PRIVATE COYIN_NATIVE_WITH_QT=1)
endif()

if (MSVC)
    target_compile_options(coyin_native PRIVATE /utf-8)
endif()

set_target_properties(coyin_native PROPERTIES
    OUTPUT_NAME "coyin_native"
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)
