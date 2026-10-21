#include <string>

// First native module: a tiny health/version function. Later phases can expose
// performance-sensitive C++ code to Python through pybind11 or a C ABI.
#if defined(_WIN32)
  #define ULTRON_API __declspec(dllexport)
#else
  #define ULTRON_API __attribute__((visibility("default")))
#endif

extern "C" ULTRON_API const char* ultron_native_version() {
    return "ULTRON native core 0.1.0 (C++17)";
}
