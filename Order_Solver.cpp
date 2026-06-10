#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <map>
#include <set>
#include <queue>
#include <tuple>
#include <algorithm>
#include <sstream>

#ifdef _WIN32
#include <windows.h>
#endif

using namespace std;

// === 定数・色マッピング ===
const int CAPACITY = 4;
const int UNKNOWN = -1;
const int SEALED = -2;
const int ANY_COLOR = -3;

int color_to_int(const string& c) {
    if(c == "？") return -1;
    if(c == "封") return -2;
    if(c == "無") return -3;
    if(c == "赤") return 0;
    if(c == "青") return 1;
    if(c == "水") return 2;
    if(c == "緑") return 3;
    if(c == "黄") return 4;
    if(c == "橙") return 5;
    if(c == "紫") return 6;
    if(c == "白") return 7;
    return -99;
}

string int_to_color(int c) {
    switch(c) {
        case -1: return "？"; case -2: return "封"; case -3: return "無";
        case 0: return "赤";  case 1: return "青";  case 2: return "水";
        case 3: return "緑";  case 4: return "黄";  case 5: return "橙";
        case 6: return "紫";  case 7: return "白";  default: return " ";
    }
}

// === データ構造 ===
typedef vector<int> Bottle;
typedef vector<Bottle> State;

struct StateHash {
    size_t operator()(const State& s) const {
        size_t h = 0;
        for (const auto& b : s) {
            size_t bh = 0;
            for (int c : b) bh = bh * 31 + c;
            h = h * 31 + bh;
        }
        return h;
    }
};

struct MoveInfo {
    int src, dst, amount, color;
};

struct Node {
    int f_cost, g_cost, tie_breaker;
    State state;
    vector<MoveInfo> path;
    bool operator>(const Node& other) const {
        if (f_cost != other.f_cost) return f_cost > other.f_cost;
        if (g_cost != other.g_cost) return g_cost > other.g_cost;
        return tie_breaker > other.tie_breaker;
    }
};

// === 基本ロジック ===
pair<int, int> get_top_info(const Bottle& bottle) {
    if(bottle.empty()) return {-99, 0};
    int top_color = bottle.back();
    if(top_color == UNKNOWN || top_color == SEALED) return {top_color, 0};
    int count = 0;
    for(int i = bottle.size()-1; i >= 0; --i) {
        if(bottle[i] == top_color) count++; else break;
    }
    return {top_color, count};
}

State apply_path_to_state(State state, const vector<MoveInfo>& path, int steps, const map<pair<int, int>, int>& memory) {
    for(int step = 0; step < min(steps, (int)path.size()); ++step) {
        int src = path[step].src, dst = path[step].dst, amount = path[step].amount, color = path[step].color;
        for(int a=0; a<amount; ++a) if(!state[src].empty()) state[src].pop_back();
        
        while(!state[src].empty() && state[src].back() == UNKNOWN) {
            int layer = state[src].size() - 1;
            if(memory.count({src, layer})) state[src].back() = memory.at({src, layer});
            else break;
        }
        for(int a=0; a<amount; ++a) state[dst].push_back(color);
    }
    return state;
}

void check_and_apply_unlocks(State& state_list, const vector<tuple<int, int, int>>& internal_closed,
                             const map<int, Bottle>& known_cups, const map<pair<int, int>, int>& memory) {
    map<int, int> completed_counts;
    int total_completed = 0;
    for(const auto& b : state_list) {
        if(b.size() == CAPACITY) {
            bool all_same = true;
            for(int c : b) if(c != b[0]) { all_same = false; break; }
            if(all_same && b[0] >= 0) { completed_counts[b[0]]++; total_completed++; }
        }
    }

    for(auto& rule : internal_closed) {
        int idx = get<0>(rule), col_id = get<1>(rule), req = get<2>(rule);
        if(!state_list[idx].empty() && state_list[idx][0] == SEALED) {
            bool met = (col_id == ANY_COLOR) ? (total_completed >= req) : (completed_counts[col_id] >= req);
            if(met) {
                if(known_cups.count(idx)) {
                    Bottle temp_b = known_cups.at(idx);
                    while(!temp_b.empty() && temp_b.back() == UNKNOWN) {
                        int l = temp_b.size() - 1;
                        if(memory.count({idx, l})) temp_b.back() = memory.at({idx, l});
                        else break;
                    }
                    state_list[idx] = temp_b;
                } else {
                    state_list[idx] = {UNKNOWN};
                }
            }
        }
    }
}

vector<tuple<State, MoveInfo, int>> get_possible_moves(
    const State& state, const set<int>& target_colors, const vector<tuple<int, int, int>>& internal_closed,
    const map<pair<int, int>, int>& memory, const map<int, Bottle>& known_cups, bool simulate_unlocks) 
{
    set<int> closed_indexes;
    for(auto& r : internal_closed) closed_indexes.insert(get<0>(r));
    vector<tuple<State, MoveInfo, int>> next_states;

    for(int i=0; i<state.size(); ++i) {
        if(closed_indexes.count(i) || state[i].empty() || state[i][0] == SEALED) continue;
        
        bool all_same = true;
        for(int c : state[i]) if(c != state[i][0]) all_same = false;
        if(state[i].size() == CAPACITY && all_same) continue;

        auto top_info = get_top_info(state[i]);
        int src_color = top_info.first, src_count = top_info.second;
        if(src_color < 0 || src_count == 0) continue;

        for(int j=0; j<state.size(); ++j) {
            if(i == j || closed_indexes.count(j) || (!state[j].empty() && state[j][0] == SEALED) || state[j].size() == CAPACITY) continue;
            if(state[j].empty() && src_count == state[i].size()) continue;

            auto dst_info = get_top_info(state[j]);
            if(state[j].empty() || dst_info.first == src_color) {
                int space = CAPACITY - state[j].size();
                int move_amount = min(src_count, space);

                State new_state = state;
                for(int a=0; a<move_amount; ++a) new_state[i].pop_back();

                while(!new_state[i].empty() && new_state[i].back() == UNKNOWN) {
                    int layer = new_state[i].size() - 1;
                    if(memory.count({i, layer})) new_state[i].back() = memory.at({i, layer});
                    else break;
                }

                for(int a=0; a<move_amount; ++a) new_state[j].push_back(src_color);

                if(simulate_unlocks) check_and_apply_unlocks(new_state, internal_closed, known_cups, memory);

                int action_cost = 10;
                if(!new_state[i].empty() && new_state[i].back() >= 0) {
                    int a_top = new_state[i].back();
                    bool has_empty = false, has_match = false;
                    for(int k=0; k<new_state.size(); ++k) {
                        if(new_state[k].empty()) has_empty = true;
                        if(k != i && !new_state[k].empty() && new_state[k][0] != SEALED && new_state[k].back() == a_top) has_match = true;
                    }
                    if(!has_empty && !has_match) action_cost += 100;
                }

                if(!target_colors.empty()) {
                    if(target_colors.count(src_color) || target_colors.count(ANY_COLOR)) {
                        bool dst_full = (new_state[j].size() == CAPACITY);
                        for(int c : new_state[j]) if(c != src_color) dst_full = false;
                        action_cost = dst_full ? 0 : 2;
                    }
                }
                next_states.push_back({new_state, {i, j, move_amount, src_color}, action_cost});
            }
        }
    }
    return next_states;
}

bool is_cleared(const State& state) {
    for(auto& b : state) {
        if(b.empty() || b[0] == SEALED) continue;
        if(b.size() != CAPACITY || b[0] == UNKNOWN) return false;
        for(int c : b) if(c != b[0]) return false;
    }
    return true;
}

int count_exposed_unknowns(const State& state) {
    int count = 0;
    for(auto& b : state) if(!b.empty() && b.back() == UNKNOWN) count++;
    return count;
}

int count_completed(const State& state, int target_id) {
    int count = 0;
    for(auto& b : state) {
        if(b.size() == CAPACITY && b[0] >= 0) {
            bool all_same = true;
            for(int c : b) if(c != b[0]) all_same = false;
            if(all_same && (target_id == ANY_COLOR || b[0] == target_id)) count++;
        }
    }
    return count;
}

int get_heuristic(const State& state, const set<int>& target_colors) {
    int h_cost = 0;
    for(auto& b : state) if(!b.empty() && b[0] == SEALED) h_cost += 500;
    if(!target_colors.empty()) {
        int max_comp = 0;
        for(int tid : target_colors) max_comp = max(max_comp, count_completed(state, tid));
        h_cost -= max_comp * 200;
    }
    return h_cost;
}

// === 探索（solve） ===
pair<vector<MoveInfo>, State> solve(State state, string mode, set<int> target_colors, 
                                    vector<tuple<int, int, int>> internal_closed,
                                    map<pair<int, int>, int> memory_int, map<int, Bottle> known_cups, bool simulate_unlocks) 
{
    for(int i=0; i<state.size(); ++i) {
        while(!state[i].empty() && state[i].back() == UNKNOWN) {
            int l = state[i].size() - 1;
            if(memory_int.count({i, l})) state[i].back() = memory_int[{i, l}];
            else break;
        }
    }

    int tie_breaker = 0;
    priority_queue<Node, vector<Node>, greater<Node>> pq;
    pq.push({get_heuristic(state, target_colors), 0, tie_breaker++, state, {}});
    
    unordered_map<State, int, StateHash> visited;
    visited[state] = 0;
    
    int initial_unknowns = count_exposed_unknowns(state);
    int initial_closed_count = 0;
    for(auto& b : state) if(!b.empty() && b[0] == SEALED) initial_closed_count++;
    
    map<int, int> initial_completions;
    for(int tid : target_colors) initial_completions[tid] = count_completed(state, tid);
    
    int iter_count = 0, MAX_ITER = 300000;

    while(!pq.empty()) {
        iter_count++;
        Node curr = pq.top(); pq.pop();

        if (iter_count % 10000 == 0) cout << "\r⏳ 計算中... (探索済み: " << visited.size() << " | 深さ: " << curr.path.size() << ") " << flush;

        if (mode == "prioritize" && !target_colors.empty()) {
            for(int tid : target_colors) {
                if(count_completed(curr.state, tid) > initial_completions[tid]) { cout << endl; return {curr.path, curr.state}; }
            }
        } else if (mode == "clear" && is_cleared(curr.state)) {
            cout << endl; return {curr.path, curr.state};
        } else if (mode == "reveal") {
            if (count_exposed_unknowns(curr.state) > initial_unknowns) { cout << endl; return {curr.path, curr.state}; }
        } else if (mode == "unlock_reveal") {
            if (count_exposed_unknowns(curr.state) > initial_unknowns) { cout << endl; return {curr.path, curr.state}; }
            int curr_closed = 0;
            for(auto& b : curr.state) if(!b.empty() && b[0] == SEALED) curr_closed++;
            if (curr_closed < initial_closed_count) { cout << endl; return {curr.path, curr.state}; }
        }

        auto next_moves = get_possible_moves(curr.state, target_colors, internal_closed, memory_int, known_cups, simulate_unlocks);
        for(auto& mv : next_moves) {
            State next_st = get<0>(mv);
            int action_cost = get<2>(mv);
            int new_g = curr.g_cost + action_cost;
            if(visited.find(next_st) == visited.end() || new_g < visited[next_st]) {
                visited[next_st] = new_g;
                vector<MoveInfo> new_path = curr.path;
                new_path.push_back(get<1>(mv));
                pq.push({new_g + get_heuristic(next_st, target_colors), new_g, tie_breaker++, next_st, new_path});
            }
        }
    }
    cout << endl; return {{}, {}};
}

// === CUI 入出力・エクスポート ===
string get_input(string prompt) {
    cout << prompt;
    string s; getline(cin, s);
    return s;
}

void print_board(const State& state, const vector<int>& layout, const vector<tuple<int, int, int>>& internal_closed) {
    set<int> closed_indexes;
    for(auto& r : internal_closed) closed_indexes.insert(get<0>(r));
    int max_rows = 0; for(int h : layout) max_rows = max(max_rows, h);

    cout << "\n=================================================\n【 現在の盤面状態 】\n=================================================\n";
    for (int r = 0; r < max_rows; ++r) {
        for (int layer = CAPACITY - 1; layer >= 0; --layer) {
            for (int c = 0; c < layout.size(); ++c) {
                if (r < layout[c]) {
                    int idx = 0; for(int k=0; k<c; ++k) idx += layout[k]; idx += r;
                    if (layer < state[idx].size()) {
                        string color = int_to_color(state[idx][layer]);
                        if(color == "封") cout << "[ 封 ] "; 
                        else cout << "[ " << color << " ] ";
                    } else cout << "[    ] ";
                } else cout << "       ";
            }
            cout << "\n";
        }
        for (int c = 0; c < layout.size(); ++c) {
            if (r < layout[c]) cout << "------ ";
            else cout << "       ";
        }
        cout << "\n";
        for (int c = 0; c < layout.size(); ++c) {
            if (r < layout[c]) {
                int idx = 0; for(int k=0; k<c; ++k) idx += layout[k]; idx += r;
                if(closed_indexes.count(idx)) printf(" 閉%02d  ", idx); 
                else printf("  %02d   ", idx);
            } else cout << "       ";
        }
        cout << "\n\n";
    }
}

void export_board(const State& board, const vector<int>& layout, const map<pair<int, int>, int>& memory, const map<int, Bottle>& cups) {
    cout << "\n★ C++ソースコード (OrderSolver.cpp) 更新用データ ★\n";
    cout << "以下の設定を main 関数の中にコピペして再コンパイルしてください。\n\n";
    cout << "    known_memory = {\n";
    for(auto& kv : memory) cout << "        {{" << kv.first.first << ", " << kv.first.second << "}, color_to_int(\"" << int_to_color(kv.second) << "\")},\n";
    cout << "    };\n    known_cup_contents = {\n";
    for(auto& kv : cups) {
        cout << "        {" << kv.first << ", {";
        for(int i=0; i<kv.second.size(); ++i) cout << "color_to_int(\"" << int_to_color(kv.second[i]) << "\")" << (i+1==kv.second.size() ? "" : ", ");
        cout << "}},\n";
    }
    cout << "    };\n    initial_board = {\n";
    int idx = 0;
    for(int c=0; c<layout.size(); ++c) {
        cout << "        // --- 列 " << c << " ---\n";
        for(int r=0; r<layout[c]; ++r) {
            cout << "        {";
            for(int i=0; i<board[idx].size(); ++i) {
                if(board[idx][i] == UNKNOWN) cout << "UNKNOWN";
                else if(board[idx][i] == SEALED) cout << "SEALED";
                else cout << "color_to_int(\"" << int_to_color(board[idx][i]) << "\")";
                if(i+1 != board[idx].size()) cout << ", ";
            }
            cout << "}, // " << idx++ << "\n";
        }
        cout << "\n";
    }
    cout << "    };\n\n";
}

// === メインのインタラクティブ・ループ ===
void interactive_solver(State base_board, vector<int> layout, vector<tuple<int, string, int>> closed_rules, 
                        map<pair<int, int>, int> memory_str, map<int, Bottle> known_cups) 
{
    set<int> target_colors;

    while(true) {
        vector<tuple<int, int, int>> internal_closed;
        for(auto& r : closed_rules) internal_closed.push_back({get<0>(r), color_to_int(get<1>(r)), get<2>(r)});
        
        State current_state = base_board;
        cout << "\n★★★★★★★★★★★★★★★★★★★★★★★★★★\n【 新しい探索（またはリスタート）を開始します 】\n★★★★★★★★★★★★★★★★★★★★★★★★★★\n";

        while(true) {
            for(int i=0; i<current_state.size(); ++i) {
                while(!current_state[i].empty() && current_state[i].back() == UNKNOWN) {
                    int l = current_state[i].size() - 1;
                    if(memory_str.count({i, l})) current_state[i].back() = memory_str[{i, l}];
                    else break;
                }
            }
            print_board(current_state, layout, internal_closed);
            
            set<int> closed_indexes;
            for(auto& r : internal_closed) closed_indexes.insert(get<0>(r));
            
            vector<int> exposed;
            for(int i=0; i<current_state.size(); ++i) {
                if(!current_state[i].empty() && current_state[i].back() == UNKNOWN) {
                    if(closed_indexes.count(i) == 0) {
                        exposed.push_back(i);
                    }
                }
            }
            
            if(!exposed.empty()) {
                cout << "💡 新しい '？' が見つかりました。\n";
                bool skip_input = false;
                bool updated = false;
                for(int i : exposed) {
                    char buf[100];
                    sprintf(buf, "▶ ボトル %02d の '？' の色が判明しました！何色ですか？ (s:スキップ, q:終了): ", i);
                    string new_color = get_input(buf);
                    
                    if(new_color == "q" || new_color == "Q") return;
                    if(new_color == "s" || new_color == "S") { skip_input = true; break; }
                    
                    int col_int = color_to_int(new_color);
                    if(col_int >= 0) {
                        int layer = current_state[i].size() - 1;
                        memory_str[{i, layer}] = col_int; 
                        current_state[i].back() = col_int; 
                        updated = true;
                    } else {
                        cout << "⚠️ 無効な色です。スキップします。\n";
                        skip_input = true; break;
                    }
                }
                if(updated && !skip_input) {
                    for(int i : exposed) {
                        int layer = current_state[i].size() - 1;
                        if (layer >= 0 && current_state[i][layer] != UNKNOWN && layer < base_board[i].size()) {
                            base_board[i][layer] = current_state[i][layer];
                        }
                    }
                    continue; 
                }
            }

            map<int, int> completed_counts;
            int total_completed = 0;
            for(auto& b : current_state) {
                if(b.size() == CAPACITY) {
                    bool all_same = true;
                    for(int c : b) if(c != b[0]) all_same = false;
                    if(all_same && b[0] >= 0) { completed_counts[b[0]]++; total_completed++; }
                }
            }

            vector<tuple<int, int, string>> unmet_rules;
            for(auto& r : internal_closed) {
                int idx = get<0>(r), col_id = get<1>(r), req = get<2>(r);
                if(col_id == ANY_COLOR) {
                    if(total_completed < req) unmet_rules.push_back({idx, col_id, "無（何色でも）"});
                } else {
                    if(completed_counts[col_id] < req) unmet_rules.push_back({idx, col_id, int_to_color(col_id)});
                }
            }

            set<int> target_colors_for_solve = target_colors;
            pair<vector<MoveInfo>, State> res;

            if(!target_colors.empty()) {
                cout << "探索開始: [手動] 指定された色の完成を最優先で計算中...\n";
                res = solve(current_state, "prioritize", target_colors_for_solve, internal_closed, memory_str, known_cups, true);
            } else {
                cout << "探索開始: [フェーズ1] 盤面の '？' の開拓を目標に計算中...\n";
                res = solve(current_state, "reveal", {}, internal_closed, memory_str, known_cups, false);
                
                if(res.first.empty() && !unmet_rules.empty()) {
                    cout << "\n⚠️ 現在の盤面ではこれ以上 '？' を開拓できません。\n➡️ [フェーズ2] カップを開封し、連鎖的に盤面を広げて『？』を露出させるルートを計算します。\n【 開放候補のカップ 】\n";
                    for(auto& r : unmet_rules) cout << "  - ボトル " << get<0>(r) << " (条件: " << get<2>(r) << ")\n";
                    
                    string choice = get_input("優先して開けたいカップの番号を入力 (そのままEnterで自動探索): ");
                    if(!choice.empty()) {
                        int c_idx = stoi(choice);
                        for(auto& r : unmet_rules) if(get<0>(r) == c_idx) target_colors_for_solve.insert(get<1>(r));
                    }
                    if(target_colors_for_solve.empty()) for(auto& r : unmet_rules) target_colors_for_solve.insert(get<1>(r));
                    
                    cout << "\n探索開始: [フェーズ2移行] 封印解除を通じて『？』を露出させるルートを計算中...\n";
                    res = solve(current_state, "unlock_reveal", target_colors_for_solve, internal_closed, memory_str, known_cups, true);

                    if(res.first.empty()) {
                        cout << "\n⚠️ どのカップを解除するルートも見つかりませんでした。\n➡️ [フェーズ3] 可能な範囲で盤面を整理し、クリアを目指すルートを検索します...\n";
                        res = solve(current_state, "clear", {}, internal_closed, memory_str, known_cups, true);
                    }
                } else if(res.first.empty() && unmet_rules.empty()) {
                    cout << "探索開始: [フェーズ3] 【全条件達成】全クリアに向けて最短ルートを計算中...\n";
                    res = solve(current_state, "clear", {}, internal_closed, memory_str, known_cups, true);
                }
            }

            vector<MoveInfo> path = res.first;
            if(path.empty()) {
                cout << "\n❌ 手詰まりです。これ以上、目標を達成できる手順が見つかりません。\n";
            } else {
                cout << "✅ 最良 " << path.size() << " 手の手順が見つかりました！\n";
                for(int i=0; i<path.size(); ++i) cout << "  手順 " << i+1 << ": ボトル " << path[i].src << " から ボトル " << path[i].dst << " へ [" << int_to_color(path[i].color) << "] を " << path[i].amount << " つ移動\n";
                cout << "\n💡 【重要】手順の途中でカップが開いた場合は、そこで実行を止めて [U] コマンドで盤面を同期し、再計算させてください！\n";
            }

            bool restart_flag = false;
            while(true) {
                string action = get_input("\n[Enter]:次へ  [R]:リスタート  [U]:実機ロック解除  [E]:編集  [S]:状況確認  [X]:データ出力  [Q]:終了\n-> ");
                for(char& c : action) c = tolower(c);

                if(action == "s") {
                    cout << "\n=================================================";
                    cout << "\n【 状況確認：判明済みの色をすべて反映した盤面 】";
                    cout << "\n=================================================\n";
                    
                    // ★【新機能】現在の全ボトルに対し、隠れている層も含めて記憶されている色を全て流し込んだ「可視化用状態」を生成
                    State visual_state = base_board; // リスタート用初期状態をベースにする
                    if(!path.empty()) {
                        // 手順の進行指示があった場合は、そこまでの進行分を反映
                        string steps_str = get_input("（確認）現在の手順を何手目まで進めた状態の盤面を見ますか？(0〜" + to_string(path.size()) + "): ");
                        int steps = steps_str.empty() ? 0 : stoi(steps_str);
                        visual_state = apply_path_to_state(current_state, path, steps, memory_str);
                    }
                    
                    // すべての『？』レイヤーに対して、記憶があれば「強制置換」をかける
                    for (int i = 0; i < visual_state.size(); ++i) {
                        for (int layer = 0; layer < visual_state[i].size(); ++layer) {
                            if (visual_state[i][layer] == UNKNOWN && memory_str.count({i, layer})) {
                                visual_state[i][layer] = memory_str[{i, layer}];
                            }
                        }
                    }

                    // グリッド描画（記憶置換版）
                    int max_rows = 0; for(int h : layout) max_rows = max(max_rows, h);
                    for (int r = 0; r < max_rows; ++r) {
                        for (int layer = CAPACITY - 1; layer >= 0; --layer) {
                            for (int c = 0; c < layout.size(); ++c) {
                                if (r < layout[c]) {
                                    int idx = 0; for(int k=0; k<c; ++k) idx += layout[k]; idx += r;
                                    if (layer < visual_state[idx].size()) {
                                        int col_id = visual_state[idx][layer];
                                        string color = int_to_color(col_id);
                                        
                                        // 元々『？』だった場所（＝初期盤面でUNKNOWN、かつ記憶にある場所）はアスタリスク付きで強調
                                        if (layer < base_board[idx].size() && base_board[idx][layer] == UNKNOWN && col_id >= 0) {
                                            cout << "[ " << color << " ] ";
                                        } else {
                                            if(color == "封") cout << "[ 封 ] "; 
                                            else cout << "[ " << color << " ] ";
                                        }
                                    } else cout << "[    ] ";
                                } else cout << "       ";
                            }
                            cout << "\n";
                        }
                        for (int c = 0; c < layout.size(); ++c) { if (r < layout[c]) cout << "------ "; else cout << "       "; }
                        cout << "\n";
                        for (int c = 0; c < layout.size(); ++c) {
                            if (r < layout[c]) {
                                int idx = 0; for(int k=0; k<c; ++k) idx += layout[k]; idx += r;
                                if(closed_indexes.count(idx)) printf(" 閉%02d  ", idx); else printf("  %02d   ", idx);
                            } else cout << "       ";
                        }
                        cout << "\n\n";
                    }
                    cout << "💡 補足: *色* 表記の箇所は、元々「？」だった場所を記憶から視覚化したものです。\n";
                    if(internal_closed.empty() == false) {
                        cout << "\n🔒 【 ロック(閉)の解除待ち条件 】\n";
                        for(auto& r : internal_closed) {
                            int idx = get<0>(r), col_id = get<1>(r), req = get<2>(r);
                            string col_name = (col_id == ANY_COLOR) ? "無（何色でも）" : int_to_color(col_id);
                            cout << "  ボトル " << idx << " -> 条件: " << col_name << " を " << req << " 本完成\n";
                        }
                    }
                    cout << "=================================================\n";
                    continue;
                } else if(action == "x") {
                    export_board(base_board, layout, memory_str, known_cups);
                    continue;
                } else if(action == "q") {
                    return;
                } else if(action == "r") {
                    restart_flag = true; break;
                } else if(action == "u") {
                    if(!path.empty()) {
                        string steps_str = get_input("\n何手目まで実行したところでカップが開きましたか？ (0〜" + to_string(path.size()) + "): ");
                        int steps = steps_str.empty() ? path.size() : stoi(steps_str);
                        if(steps > 0) {
                            current_state = apply_path_to_state(current_state, path, steps, memory_str);
                            cout << "\n➡️ 盤面を " << steps << " 手進めた状態に同期しました。\n";
                        }
                    }
                    int u_idx = stoi(get_input("\n実機で解放されたボトルの番号を入力: "));
                    if(!current_state[u_idx].empty() && current_state[u_idx][0] == SEALED) {
                        if(known_cups.count(u_idx)) {
                            cout << "💡 記憶から復元します！\n";
                            current_state[u_idx] = known_cups[u_idx];
                        } else {
                            string b_str = get_input("最初の中身を下から順にカンマ区切りで入力: ");
                            Bottle nb;
                            stringstream ss(b_str); string item;
                            while(getline(ss, item, ',')) {
                                item.erase(remove_if(item.begin(), item.end(), ::isspace), item.end());
                                if(!item.empty()) nb.push_back(color_to_int(item));
                            }
                            known_cups[u_idx] = nb;
                            current_state[u_idx] = nb;
                        }
                        base_board[u_idx] = current_state[u_idx];
                        vector<tuple<int, int, int>> new_closed;
                        for(auto& r : internal_closed) if(get<0>(r) != u_idx) new_closed.push_back(r);
                        internal_closed = new_closed;
                    }
                    break;
                } else {
                    current_state = res.second;
                    break;
                }
            }
            if(restart_flag) break;
        }
    }
}

// ==========================================
// 実行部分
// ==========================================
int main() {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
#endif

    vector<int> LAYOUT = {3, 3, 4, 3, 4, 3, 3};
    
    map<pair<int, int>, int> known_memory = {
        {{0, 1}, color_to_int("赤")},
        {{0, 2}, color_to_int("緑")},
        {{1, 0}, color_to_int("橙")},
        {{1, 1}, color_to_int("紫")},
        {{1, 2}, color_to_int("黄")},
        {{2, 0}, color_to_int("水")},
        {{2, 1}, color_to_int("橙")},
        {{2, 2}, color_to_int("水")},
        {{3, 0}, color_to_int("白")},
        {{3, 1}, color_to_int("緑")},
        {{4, 0}, color_to_int("白")},
        {{4, 1}, color_to_int("紫")},
        {{6, 0}, color_to_int("黄")},
        {{6, 1}, color_to_int("紫")},
        {{8, 0}, color_to_int("赤")},
        {{8, 1}, color_to_int("緑")},
        {{10, 0}, color_to_int("緑")},
        {{10, 1}, color_to_int("紫")},
        {{11, 0}, color_to_int("黄")},
        {{11, 1}, color_to_int("白")},
        {{12, 0}, color_to_int("赤")},
        {{12, 1}, color_to_int("赤")},
        {{12, 2}, color_to_int("青")},
        {{15, 1}, color_to_int("白")},
        {{17, 1}, color_to_int("赤")},
        {{17, 2}, color_to_int("緑")},
        {{18, 0}, color_to_int("赤")},
        {{18, 1}, color_to_int("赤")},
        {{20, 0}, color_to_int("黄")},
        {{20, 1}, color_to_int("青")},
        {{20, 2}, color_to_int("水")},
        {{21, 0}, color_to_int("橙")},
        {{21, 1}, color_to_int("青")},
        {{21, 2}, color_to_int("水")},
        {{22, 0}, color_to_int("赤")},
        {{22, 1}, color_to_int("水")},
        {{22, 2}, color_to_int("黄")},
    };
    
    map<int, Bottle> known_cup_contents = {};
    
    vector<tuple<int, string, int>> closed = {
        {5, "黄", 2}, {19, "青", 2}
    };

    State initial_board = {
        // --- 列 0 (左から 1 列目) ---
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("白")}, // 00
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("白")}, // 01
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("赤")}, // 02

        // --- 列 1 (左から 2 列目) ---
        {UNKNOWN, UNKNOWN, color_to_int("黄"), color_to_int("黄")}, // 03
        {UNKNOWN, UNKNOWN, color_to_int("緑"), color_to_int("水")}, // 04
        {SEALED, SEALED, SEALED, SEALED}, // 05 (※修正: 条件待ちカップのため封印状態)

        // --- 列 2 (左から 3 列目) ---
        {UNKNOWN, UNKNOWN, color_to_int("赤"), color_to_int("青")}, // 06
        {SEALED, SEALED, SEALED, SEALED}, // 07 (※動画ボトル)
        {UNKNOWN, UNKNOWN, color_to_int("青"), color_to_int("青")}, // 08
        {color_to_int("赤"), color_to_int("紫")}, // 09

        // --- 列 3 (左から 4 列目) ---
        {UNKNOWN, UNKNOWN, color_to_int("黄"), color_to_int("赤")}, // 10
        {UNKNOWN, UNKNOWN, color_to_int("橙"), color_to_int("青")}, // 11
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("橙")}, // 12

        // --- 列 4 (左から 5 列目) ---
        {UNKNOWN, UNKNOWN, color_to_int("緑"), color_to_int("青")}, // 13
        {SEALED, SEALED, SEALED, SEALED}, // 14 (※動画ボトル)
        {UNKNOWN, UNKNOWN, color_to_int("橙"), color_to_int("青")}, // 15
        {color_to_int("黄"), color_to_int("橙")}, // 16

        // --- 列 5 (左から 6 列目) ---
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("黄")}, // 17
        {UNKNOWN, UNKNOWN, color_to_int("橙"), color_to_int("紫")}, // 18
        {SEALED, SEALED, SEALED, SEALED}, // 19

        // --- 列 6 (左から 7 列目) ---
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("黄")}, // 20 (※番号修正)
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("紫")}, // 21 (※番号修正)
        {UNKNOWN, UNKNOWN, UNKNOWN, color_to_int("水")}, // 22 (※番号修正)
    };

    interactive_solver(initial_board, LAYOUT, closed, known_memory, known_cup_contents);
    return 0;
}