#include <algorithm>
#include <sstream>
#include <string>
#include <vector>

namespace {

std::wstring sanitize(const std::wstring& value)
{
    std::wstring result = value;
    std::replace(result.begin(), result.end(), L'\t', L' ');
    std::replace(result.begin(), result.end(), L'\n', L' ');
    std::replace(result.begin(), result.end(), L'\r', L' ');
    return result;
}

std::vector<std::wstring> split(const std::wstring& value, wchar_t separator)
{
    std::vector<std::wstring> parts;
    std::wstringstream stream(value);
    std::wstring item;
    while (std::getline(stream, item, separator)) {
        parts.push_back(item);
    }
    return parts;
}

bool truthy(const std::wstring& value)
{
    return value == L"1" || value == L"true" || value == L"True";
}

struct LibraryRow {
    std::wstring id;
    bool favorite = false;
    std::wstring last_opened;
    std::wstring year;
    std::wstring title;
};

struct SearchRow {
    std::wstring id;
    bool has_pdf = false;
    std::wstring year;
    std::wstring title;
};

struct AnalysisRow {
    std::wstring id;
    std::wstring created_at;
    std::wstring title;
};

std::wstring join_ids(const std::vector<std::wstring>& ids)
{
    std::wstring output;
    for (size_t index = 0; index < ids.size(); ++index) {
        output += ids[index];
        if (index + 1 < ids.size()) {
            output += L"\n";
        }
    }
    return output;
}

}  // namespace

extern "C" __declspec(dllexport) const wchar_t* coyin_library_order_ids(const wchar_t* payload)
{
    static std::wstring cache;
    std::vector<LibraryRow> rows;
    const std::wstring input = payload ? std::wstring(payload) : L"";
    for (const auto& line : split(input, L'\n')) {
        if (line.empty()) {
            continue;
        }
        const auto parts = split(line, L'\t');
        if (parts.empty()) {
            continue;
        }
        rows.push_back(LibraryRow{
            parts.size() > 0 ? parts[0] : L"",
            parts.size() > 1 ? truthy(parts[1]) : false,
            parts.size() > 2 ? parts[2] : L"",
            parts.size() > 3 ? parts[3] : L"",
            parts.size() > 4 ? sanitize(parts[4]) : L"",
        });
    }
    std::sort(rows.begin(), rows.end(), [](const LibraryRow& left, const LibraryRow& right) {
        if (left.favorite != right.favorite) {
            return left.favorite > right.favorite;
        }
        if (left.last_opened != right.last_opened) {
            return left.last_opened > right.last_opened;
        }
        if (left.year != right.year) {
            return left.year > right.year;
        }
        return left.title < right.title;
    });
    std::vector<std::wstring> ids;
    for (const auto& row : rows) {
        ids.push_back(row.id);
    }
    cache = join_ids(ids);
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_search_order_ids(const wchar_t* payload)
{
    static std::wstring cache;
    std::vector<SearchRow> rows;
    const std::wstring input = payload ? std::wstring(payload) : L"";
    for (const auto& line : split(input, L'\n')) {
        if (line.empty()) {
            continue;
        }
        const auto parts = split(line, L'\t');
        if (parts.empty()) {
            continue;
        }
        rows.push_back(SearchRow{
            parts.size() > 0 ? parts[0] : L"",
            parts.size() > 1 ? truthy(parts[1]) : false,
            parts.size() > 2 ? parts[2] : L"",
            parts.size() > 3 ? sanitize(parts[3]) : L"",
        });
    }
    std::sort(rows.begin(), rows.end(), [](const SearchRow& left, const SearchRow& right) {
        if (left.has_pdf != right.has_pdf) {
            return left.has_pdf > right.has_pdf;
        }
        if (left.year != right.year) {
            return left.year > right.year;
        }
        return left.title < right.title;
    });
    std::vector<std::wstring> ids;
    for (const auto& row : rows) {
        ids.push_back(row.id);
    }
    cache = join_ids(ids);
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_analysis_order_ids(const wchar_t* payload)
{
    static std::wstring cache;
    std::vector<AnalysisRow> rows;
    const std::wstring input = payload ? std::wstring(payload) : L"";
    for (const auto& line : split(input, L'\n')) {
        if (line.empty()) {
            continue;
        }
        const auto parts = split(line, L'\t');
        if (parts.empty()) {
            continue;
        }
        rows.push_back(AnalysisRow{
            parts.size() > 0 ? parts[0] : L"",
            parts.size() > 1 ? parts[1] : L"",
            parts.size() > 2 ? sanitize(parts[2]) : L"",
        });
    }
    std::sort(rows.begin(), rows.end(), [](const AnalysisRow& left, const AnalysisRow& right) {
        if (left.created_at != right.created_at) {
            return left.created_at > right.created_at;
        }
        return left.title < right.title;
    });
    std::vector<std::wstring> ids;
    for (const auto& row : rows) {
        ids.push_back(row.id);
    }
    cache = join_ids(ids);
    return cache.c_str();
}
