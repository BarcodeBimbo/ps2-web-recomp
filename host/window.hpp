#pragma once

#include <functional>
#include <string_view>

bool open_window(bool fullscreen, std::string_view boot);
int run_window(const std::function<int()> &emulate);
