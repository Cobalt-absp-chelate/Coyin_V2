#include <algorithm>
#include <sstream>
#include <string>
#include <vector>

namespace {
std::wstring sanitize(const std::wstring& value) {
    std::wstring result = value;
    std::replace(result.begin(), result.end(), L'\t', L' ');
    std::replace(result.begin(), result.end(), L'\n', L' ');
    std::replace(result.begin(), result.end(), L'\r', L' ');
    return result;
}

std::vector<std::wstring> split(const std::wstring& value, wchar_t separator) {
    std::vector<std::wstring> parts;
    std::wstringstream stream(value);
    std::wstring item;
    while (std::getline(stream, item, separator)) {
        parts.push_back(item);
    }
    return parts;
}

bool truthy(const std::wstring& value) {
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

std::wstring join_ids(const std::vector<std::wstring>& ids) {
    std::wstring output;
    for (size_t index = 0; index < ids.size(); ++index) {
        output += ids[index];
        if (index + 1 < ids.size()) {
            output += L"\n";
        }
    }
    return output;
}
}

namespace {
std::wstring light_theme() {
    return LR"({
  "mode":"light",
  "background":"#e7ebf0",
  "workspace":"#f1f4f8",
  "workspaceTint":"#e8eef5",
  "chrome":"#f7f9fb",
  "chromeAlt":"#e9eef4",
  "panel":"#fbfcfe",
  "panelAlt":"#f3f6fa",
  "panelRaised":"#ffffff",
  "panelInset":"#ecf1f6",
  "panelHover":"#eef4fa",
  "panelFocus":"#e4edf7",
  "text":"#122033",
  "textMuted":"#4c5d70",
  "textSoft":"#708195",
  "border":"#d5dde8",
  "borderStrong":"#b9c6d8",
  "accent":"#1f5a84",
  "anchor":"#164e74",
  "accentHover":"#2d6b98",
  "accentSoft":"#dbe8f3",
  "accentSurface":"#edf4fa",
  "accentPanel":"#e4edf7",
  "accentOutline":"#88a6c1",
  "selection":"#e9dfc9",
  "success":"#506d5e",
  "warning":"#8b6c3d",
  "danger":"#8c5656",
  "note":"#efe6d4",
  "shadow":"#10243712"
})";
}

std::wstring dark_theme() {
    return LR"({
  "mode":"dark",
  "background":"#10161d",
  "workspace":"#141b24",
  "workspaceTint":"#182231",
  "chrome":"#18212b",
  "chromeAlt":"#1f2a36",
  "panel":"#1c2530",
  "panelAlt":"#243040",
  "panelRaised":"#202b37",
  "panelInset":"#16202a",
  "panelHover":"#283649",
  "panelFocus":"#314156",
  "text":"#eef3f8",
  "textMuted":"#a7b4c1",
  "textSoft":"#7f8e9d",
  "border":"#304254",
  "borderStrong":"#486078",
  "accent":"#7ba8d0",
  "anchor":"#8eb9de",
  "accentHover":"#93badb",
  "accentSoft":"#203044",
  "accentSurface":"#1d2c3c",
  "accentPanel":"#24384b",
  "accentOutline":"#5f84a7",
  "selection":"#5a4b34",
  "success":"#6d8e7b",
  "warning":"#b48d59",
  "danger":"#bb7c7c",
  "note":"#4a3f30",
  "shadow":"#00000040"
})";
}

std::wstring shell_schema() {
    return LR"({
  "primaryPages":[
    {"page_id":"home","title":"工作台","short":"工"},
    {"page_id":"library","title":"资料库","short":"库"},
    {"page_id":"search","title":"搜索","short":"搜"},
    {"page_id":"analysis","title":"分析","short":"析"}
  ],
  "utilityPages":[
    {"page_id":"settings","title":"设置"}
  ]
})";
}

std::wstring model_contracts() {
    return LR"({
  "homePath":{
    "roles":["path_id","title","caption","detail","badge","page_id","action_id","action_label","mark","tone"],
    "primaryKey":"path_id",
    "sort":[{"field":"title","order":"asc"}]
  },
  "homeMetric":{
    "roles":["metric_id","label","value","detail","tone"],
    "primaryKey":"metric_id",
    "sort":[{"field":"metric_id","order":"asc"}]
  },
  "library":{
    "roles":["document_id","display_title","kind","kind_label","authors","year","source","source_label","group_id","group_color","progress","excerpt","annotation_count","metadata_summary","favorite","last_opened","status_line"],
    "primaryKey":"document_id",
    "sort":[
      {"field":"favorite","order":"desc"},
      {"field":"last_opened","order":"desc"},
      {"field":"year","order":"desc"},
      {"field":"display_title","order":"asc"}
    ],
    "emptyTitle":"当前资料视图",
    "emptySummary":"当前筛选下无结果。"
  },
  "searchSource":{
    "roles":["source_id","label","result_count","available_count","summary"],
    "primaryKey":"source_id",
    "sort":[{"field":"label","order":"asc"}]
  },
  "searchResult":{
    "roles":["result_id","title","authors","year","item_type","abstract_text","source_id","source_label","landing_url","pdf_url","venue","doi","has_pdf","meta_summary","status_line"],
    "primaryKey":"result_id",
    "sort":[
      {"field":"has_pdf","order":"desc"},
      {"field":"year","order":"desc"},
      {"field":"title","order":"asc"}
    ],
    "emptyTitle":"结果状态",
    "emptySummary":"暂无检索结果。"
  },
  "analysisHistory":{
    "roles":["report_id","document_id","title","created_at","summary","reading_note","latex_snippet","field_count","experiment_count","comparison_count","status_line"],
    "primaryKey":"report_id",
    "sort":[{"field":"created_at","order":"desc"}]
  },
  "plugin":{
    "roles":["plugin_id","name","version","author","description","builtin","plugin_enabled","default_enabled","capabilities","load_error","state_label"],
    "primaryKey":"plugin_id",
    "sort":[
      {"field":"plugin_enabled","order":"desc"},
      {"field":"builtin","order":"desc"},
      {"field":"name","order":"asc"}
    ]
  },
  "group":{
    "roles":["group_id","name","group_color","document_count","summary"],
    "primaryKey":"group_id",
    "sort":[{"field":"document_count","order":"desc"}]
  },
  "kindOption":{
    "roles":["id","label","count"],
    "primaryKey":"id",
    "sort":[{"field":"label","order":"asc"}]
  },
  "recentNote":{
    "roles":["note_id","title","content","created_at","status_line"],
    "primaryKey":"note_id",
    "sort":[{"field":"created_at","order":"desc"}]
  },
  "recentSearch":{
    "roles":["label"],
    "primaryKey":"label"
  },
  "recentLatex":{
    "roles":["session_id","title","template","path","updated_at","status_line"],
    "primaryKey":"session_id",
    "sort":[{"field":"updated_at","order":"desc"}]
  },
  "provider":{
    "roles":["provider_id","name","base_url","api_key","default_model","analysis_model","active","state_label"],
    "primaryKey":"provider_id",
    "sort":[{"field":"name","order":"asc"}]
  },
  "settingsSummary":{
    "roles":["entry_id","title","value","detail","state"],
    "primaryKey":"entry_id",
    "sort":[{"field":"title","order":"asc"}]
  }
})";
}

std::wstring model_schema() {
    return LR"({
  "homePath":["path_id","title","caption","detail","badge","page_id","action_id","action_label","mark","tone"],
  "homeMetric":["metric_id","label","value","detail","tone"],
  "library":["document_id","display_title","kind","kind_label","authors","year","source","source_label","group_id","group_color","progress","excerpt","annotation_count","metadata_summary","favorite","last_opened","status_line"],
  "searchSource":["source_id","label","result_count","available_count","summary"],
  "searchResult":["result_id","title","authors","year","item_type","abstract_text","source_id","source_label","landing_url","pdf_url","venue","doi","has_pdf","meta_summary","status_line"],
  "analysisHistory":["report_id","document_id","title","created_at","summary","reading_note","latex_snippet","field_count","experiment_count","comparison_count","status_line"],
  "plugin":["plugin_id","name","version","author","description","builtin","plugin_enabled","default_enabled","capabilities","load_error","state_label"],
  "group":["group_id","name","group_color","document_count","summary"],
  "kindOption":["id","label","count"],
  "recentNote":["note_id","title","content","created_at","status_line"],
  "recentSearch":["label"],
  "recentLatex":["session_id","title","template","path","updated_at","status_line"],
  "provider":["provider_id","name","base_url","api_key","default_model","analysis_model","active","state_label"],
  "settingsSummary":["entry_id","title","value","detail","state"]
})";
}

std::wstring task_contracts() {
    return LR"({
  "search":{
    "title":"论文检索",
    "hint":"搜索结果、导入资料库和后续分析会继续汇入同一任务管线。",
    "phases":{
      "idle":"输入关键词后检索。",
      "loading":"正在检索论文来源…",
      "refreshing":"正在刷新检索结果…",
      "ready":"检索完成。",
      "empty":"未找到匹配结果。",
      "error":"检索失败。"
    }
  },
  "analysis":{
    "title":"结构化分析",
    "hint":"分析、导出、转写作和 LaTeX 路径会继续沿用这一任务状态。",
    "phases":{
      "idle":"选择文档后开始分析。",
      "loading":"正在生成结构化分析…",
      "refreshing":"正在刷新分析报告…",
      "ready":"分析完成。",
      "empty":"当前没有可展示的分析结果。",
      "error":"分析失败。"
    }
  },
  "export":{
    "title":"导出任务",
    "hint":"写作导出、LaTeX 导出和其他外部产出会继续并入统一导出管线。",
    "phases":{
      "idle":"等待导出。",
      "loading":"正在导出…",
      "refreshing":"正在刷新导出结果…",
      "ready":"导出完成。",
      "empty":"当前没有可导出的内容。",
      "error":"导出失败。"
    }
  },
  "latex_compile":{
    "title":"LaTeX 编译",
    "hint":"编译状态、错误摘要和导出路径都会继续复用这一任务状态。",
    "phases":{
      "idle":"模板已载入，准备编译。",
      "loading":"正在编译 LaTeX…",
      "refreshing":"正在重新编译 LaTeX…",
      "ready":"编译完成。",
      "empty":"当前没有编译结果。",
      "error":"编译失败。"
    }
  }
})";
}
}

extern "C" __declspec(dllexport) const wchar_t* coyin_theme_json(const wchar_t* mode) {
    static std::wstring cache;
    const std::wstring value = mode ? std::wstring(mode) : L"light";
    cache = (value == L"dark") ? dark_theme() : light_theme();
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_shell_schema_json() {
    static std::wstring cache = shell_schema();
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_model_schema_json() {
    static std::wstring cache = model_schema();
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_model_contracts_json() {
    static std::wstring cache = model_contracts();
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_task_contracts_json() {
    static std::wstring cache = task_contracts();
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_library_order_ids(const wchar_t* payload) {
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
        if (left.favorite != right.favorite) return left.favorite > right.favorite;
        if (left.last_opened != right.last_opened) return left.last_opened > right.last_opened;
        if (left.year != right.year) return left.year > right.year;
        return left.title < right.title;
    });
    std::vector<std::wstring> ids;
    for (const auto& row : rows) ids.push_back(row.id);
    cache = join_ids(ids);
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_search_order_ids(const wchar_t* payload) {
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
        if (left.has_pdf != right.has_pdf) return left.has_pdf > right.has_pdf;
        if (left.year != right.year) return left.year > right.year;
        return left.title < right.title;
    });
    std::vector<std::wstring> ids;
    for (const auto& row : rows) ids.push_back(row.id);
    cache = join_ids(ids);
    return cache.c_str();
}

extern "C" __declspec(dllexport) const wchar_t* coyin_analysis_order_ids(const wchar_t* payload) {
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
        if (left.created_at != right.created_at) return left.created_at > right.created_at;
        return left.title < right.title;
    });
    std::vector<std::wstring> ids;
    for (const auto& row : rows) ids.push_back(row.id);
    cache = join_ids(ids);
    return cache.c_str();
}
