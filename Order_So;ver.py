import heapq
from itertools import count
import sys

# 【内部計算用の色マッピング】
COLOR_MAP = {'？': -1, '封': -2, '無': -3, '赤': 0, '青': 1, '水': 2, '緑': 3, '黄': 4, '橙': 5, '紫': 6, '白': 7}
INV_COLOR_MAP = {v: k for k, v in COLOR_MAP.items() if v >= -2}

def to_int_state(str_state):
    return tuple(tuple(COLOR_MAP[c] for c in b) for b in str_state)

def to_str_state(int_state):
    return tuple(tuple(INV_COLOR_MAP[c] for c in b) for b in int_state)

def get_top_info(bottle):
    if not bottle: return None, 0
    top_color = bottle[-1]
    if top_color in (-1, -2): return top_color, 0
    count = 0
    for i in range(len(bottle)-1, -1, -1):
        if bottle[i] == top_color: count += 1
        else: break
    return top_color, count

def apply_path_to_state_str(state, path, steps, capacity, memory_str):
    new_state = list(state)
    for step_num in range(min(steps, len(path))):
        src, dst, amount, color_str = path[step_num] 
        
        src_bottle = list(new_state[src])
        new_state[src] = tuple(src_bottle[:-amount]) if amount < len(src_bottle) else ()
        
        temp_src = list(new_state[src])
        while temp_src and temp_src[-1] == '？':
            layer = len(temp_src) - 1
            if (src, layer) in memory_str:
                temp_src[-1] = memory_str[(src, layer)]
            else:
                break
        new_state[src] = tuple(temp_src)
        
        dst_bottle = new_state[dst]
        new_state[dst] = dst_bottle + (color_str,) * amount
        
    return tuple(new_state)

def check_and_apply_unlocks(state_list, capacity, internal_closed, known_cups_int, memory_int):
    completed_counts = {}
    total_completed = 0
    for b in state_list:
        if len(b) == capacity and all(c == b[0] for c in b) and b[0] not in (-1, -2):
            completed_counts[b[0]] = completed_counts.get(b[0], 0) + 1
            total_completed += 1

    for idx, col_id, req in internal_closed:
        if state_list[idx] and state_list[idx][0] == -2:
            met = False
            if col_id == -3:
                met = total_completed >= req
            else:
                met = completed_counts.get(col_id, 0) >= req

            if met:
                if idx in known_cups_int:
                    temp_b = list(known_cups_int[idx])
                    while temp_b and temp_b[-1] == -1:
                        l = len(temp_b) - 1
                        if (idx, l) in memory_int:
                            temp_b[-1] = memory_int[(idx, l)]
                        else:
                            break
                    state_list[idx] = tuple(temp_b)
                else:
                    state_list[idx] = (-1,)

def get_possible_moves(state, capacity, target_colors=None, internal_closed=None, memory_int=None, known_cups_int=None, simulate_unlocks=False):
    if target_colors is None: target_colors = set()
    if memory_int is None: memory_int = {}
    if known_cups_int is None: known_cups_int = {}
    
    closed_indexes = {c[0] for c in internal_closed} if internal_closed else set()
    next_states = []
    
    for i in range(len(state)):
        if i in closed_indexes: continue 
        
        src = state[i]
        if not src: continue
        if src[0] == -2: continue 
        if len(src) == capacity and all(c == src[0] for c in src): continue
            
        src_color, src_count = get_top_info(src)
        if src_color in (-1, -2) or src_count == 0: continue

        for j in range(len(state)):
            if i == j: continue
            if j in closed_indexes: continue 
            
            dst = state[j]
            if dst and dst[0] == -2: continue 
            if len(dst) == capacity: continue
            if not dst and src_count == len(src): continue
            
            dst_color, _ = get_top_info(dst)
            if not dst or dst_color == src_color:
                space = capacity - len(dst)
                move_amount = min(src_count, space)
                
                new_src = src[:-move_amount] if move_amount < len(src) else ()
                
                if new_src and new_src[-1] == -1:
                    temp_src = list(new_src)
                    while temp_src and temp_src[-1] == -1:
                        layer = len(temp_src) - 1
                        if (i, layer) in memory_int:
                            temp_src[-1] = memory_int[(i, layer)]
                        else:
                            break
                    new_src = tuple(temp_src)
                
                new_dst = dst + (src_color,) * move_amount
                
                new_state = list(state)
                new_state[i] = new_src
                new_state[j] = new_dst
                
                if simulate_unlocks and internal_closed:
                    check_and_apply_unlocks(new_state, capacity, internal_closed, known_cups_int, memory_int)
                
                new_state_tuple = tuple(new_state)
                action_cost = 10 
                
                a_bottle = new_state_tuple[i]
                if a_bottle and a_bottle[-1] not in (-1, -2):
                    a_top = a_bottle[-1]
                    has_empty = any(not b for b in new_state_tuple)
                    has_match = any(k != i and b and b[0] != -2 and b[-1] == a_top for k, b in enumerate(new_state_tuple))
                    if not has_empty and not has_match:
                        action_cost += 100 
                
                if target_colors:
                    if src_color in target_colors or -3 in target_colors:
                        if len(new_dst) == capacity and all(c == src_color for c in new_dst):
                            action_cost = 0  
                        else:
                            action_cost = 2  
                        
                move_info = (i, j, move_amount, INV_COLOR_MAP[src_color])
                next_states.append((new_state_tuple, move_info, action_cost))
                
    return next_states

def is_cleared(state, capacity):
    for b in state:
        if not b: continue
        if b[0] == -2: continue
        if len(b) != capacity or len(set(b)) != 1 or b[0] == -1: return False
    return True

def get_exposed_unknowns(state):
    return [i for i, b in enumerate(state) if b and b[-1] == -1]

def count_completed(state, target_id, capacity):
    if target_id == -3:
        return sum(1 for b in state if len(b) == capacity and all(c == b[0] for c in b) and b[0] >= 0)
    if target_id is None: 
        return 0
    return sum(1 for b in state if len(b) == capacity and all(c == target_id for c in b))

def get_heuristic(state, capacity, target_colors=None):
    h_cost = 0
    closed_count = sum(1 for b in state if b and b[0] == -2)
    h_cost += closed_count * 500
    
    if target_colors:
        max_comp = 0
        for tid in target_colors:
            comp = count_completed(state, tid, capacity)
            if comp > max_comp:
                max_comp = comp
        h_cost -= max_comp * 200
        
    return h_cost

def solve(initial_str_state, capacity, mode="clear", target_colors=None, internal_closed=None, memory_str=None, known_cups_str=None, simulate_unlocks=True):
    int_state = to_int_state(initial_str_state)
    
    memory_int = {}
    if memory_str:
        for k, v in memory_str.items():
            memory_int[k] = COLOR_MAP[v]
            
    known_cups_int = {}
    if known_cups_str:
        for k, v in known_cups_str.items():
            known_cups_int[k] = tuple(COLOR_MAP[c] for c in v)
            
    initial_list = []
    for i, b in enumerate(int_state):
        temp_b = list(b)
        while temp_b and temp_b[-1] == -1:
            l = len(temp_b) - 1
            if (i, l) in memory_int:
                temp_b[-1] = memory_int[(i, l)]
            else:
                break
        initial_list.append(tuple(temp_b))
    int_state = tuple(initial_list)

    tie_breaker = count()
    
    initial_h = get_heuristic(int_state, capacity, target_colors)
    queue = [(initial_h, 0, next(tie_breaker), int_state, [])] 
    visited = {int_state: 0} 
    
    initial_unknowns = len(get_exposed_unknowns(int_state))
    initial_closed_count = sum(1 for b in int_state if b and b[0] == -2)
    
    initial_completions = {}
    if mode == "prioritize" and target_colors:
        for tid in target_colors:
            initial_completions[tid] = count_completed(int_state, tid, capacity)
            
    iteration_count = 0 
    MAX_ITER = 30000 

    while queue:
        iteration_count += 1
        f_cost, current_g_cost, _, state, path = heapq.heappop(queue)

        if iteration_count % 5000 == 0:
            print(f"\r⏳ 計算中... (探索済みパターン: {len(visited):,} | 現在の手数深さ: {len(path)})", end="", flush=True)

        if mode == "prioritize" and target_colors:
            for tid in target_colors:
                if count_completed(state, tid, capacity) > initial_completions[tid]:
                    if iteration_count >= MAX_ITER: print()
                    return path, to_str_state(state)
                    
        elif mode == "clear" and is_cleared(state, capacity):
            if iteration_count >= MAX_ITER: print()
            return path, to_str_state(state)
            
        elif mode == "reveal":
            if len(get_exposed_unknowns(state)) > initial_unknowns:
                if iteration_count >= MAX_ITER: print()
                return path, to_str_state(state)
                
        elif mode == "unlock_reveal":
            if len(get_exposed_unknowns(state)) > initial_unknowns:
                if iteration_count >= MAX_ITER: print()
                return path, to_str_state(state)
            
            current_closed_count = sum(1 for b in state if b and b[0] == -2)
            if current_closed_count < initial_closed_count:
                if iteration_count >= MAX_ITER: print()
                return path, to_str_state(state)

        for next_state, move_info, action_cost in get_possible_moves(state, capacity, target_colors, internal_closed, memory_int, known_cups_int, simulate_unlocks):
            new_g_cost = current_g_cost + action_cost
            if next_state not in visited or new_g_cost < visited[next_state]:
                visited[next_state] = new_g_cost
                
                h_cost = get_heuristic(next_state, capacity, target_colors)
                new_f_cost = new_g_cost + h_cost
                
                heapq.heappush(queue, (new_f_cost, new_g_cost, next(tie_breaker), next_state, path + [move_info]))

    if iteration_count >= MAX_ITER: print()
    return None, None

def print_board(state, capacity, layout, internal_closed=None):
    max_rows = max(layout) if layout else 0
    num_cols = len(layout)
    closed_indexes = {c[0] for c in internal_closed} if internal_closed else set()

    print("\n" + "="*(num_cols * 7))
    print(f"【 現在の盤面状態 】")
    print("="*(num_cols * 7))
    
    for r in range(max_rows):
        for layer in range(capacity - 1, -1, -1):
            row_str = ""
            for c, col_height in enumerate(layout):
                if r < col_height:
                    idx = sum(layout[:c]) + r
                    bottle = state[idx]
                    if len(bottle) > layer:
                        color = str(bottle[layer])
                        if color == '封': row_str += f"[ 封 ] "
                        else: row_str += f"[{color:^3}] " if len(color) == 1 else f"[{color:^2}] "
                    else:
                        row_str += "[    ] "
                else:
                    row_str += "       "
            print(row_str)
            
        bottom_str = ""
        num_str = ""
        for c, col_height in enumerate(layout):
            if r < col_height:
                idx = sum(layout[:c]) + r
                bottom_str += "------ "
                if idx in closed_indexes:
                    num_str += f" 閉{idx:02d}  " 
                else:
                    num_str += f"  {idx:02d}   "
            else:
                bottom_str += "       "
                num_str += "       "
        print(bottom_str)
        print(num_str)
        print() 
        
    print("="*(num_cols * 7) + "\n")

def apply_memory_to_state_str(str_state, memory_str):
    state_list = []
    for i, b in enumerate(str_state):
        temp_b = list(b)
        while temp_b and temp_b[-1] == '？':
            layer = len(temp_b) - 1
            if (i, layer) in memory_str:
                temp_b[-1] = memory_str[(i, layer)]
            else:
                break
        state_list.append(tuple(temp_b))
    return tuple(state_list)

def export_board(board, layout, memory_str, known_cup_contents):
    print("\n" + "★"*60)
    print("【 現在の盤面データ (コピペ保存用) 】")
    print("以下のブロックを全てコピーし、スクリプト下部を上書きペーストしてください。")
    print("★"*60)
    
    print("    known_memory = {")
    for (b_idx, layer), color in memory_str.items():
        print(f"        ({b_idx}, {layer}): '{color}',")
    print("    }\n")
    
    print("    known_cup_contents = {")
    for b_idx, bottle in known_cup_contents.items():
        if not bottle:
            print(f"        {b_idx}: (),")
        else:
            contents = ", ".join(f"'{color}'" for color in bottle)
            print(f"        {b_idx}: ({contents}),")
    print("    }\n")

    print("    initial_board = (")
    idx = 0
    for c, col_height in enumerate(layout):
        print(f"        # --- 列 {c} (左から {c+1} 列目) ---")
        for r in range(col_height):
            bottle = board[idx]
            if not bottle:
                print(f"        (), # {idx:02d}")
            elif len(bottle) == 1:
                print(f"        ('{bottle[0]}',), # {idx:02d}")
            else:
                contents = ", ".join(f"'{color}'" for color in bottle)
                print(f"        ({contents}), # {idx:02d}")
            idx += 1
        print()
    print("    )")
    print("★"*60 + "\n")

def interactive_solver(master_initial_board, capacity, layout, closed_rules=None, loaded_memory=None, loaded_cups=None):
    if sum(layout) != len(master_initial_board):
        print(f"\n⚠️ 【警告】 LAYOUTの合計({sum(layout)}本)と、initial_boardのボトル数({len(master_initial_board)}本)が一致していません！\n")

    base_board = master_initial_board
    target_colors = set() 
    
    memory_unknowns_str = loaded_memory if loaded_memory else {}
    known_cup_contents = loaded_cups if loaded_cups else {}
    
    while True:
        internal_closed = []
        if closed_rules:
            for idx, col_str, req in closed_rules:
                col_id = COLOR_MAP.get(col_str, -3) 
                internal_closed.append((idx, col_id, req))

        current_state = base_board
        print("\n" + "★"*50)
        print("【 新しい探索（またはリスタート）を開始します 】")
        print("★"*50)
        
        while True:
            current_state = apply_memory_to_state_str(current_state, memory_unknowns_str)
            print_board(current_state, capacity, layout, internal_closed)
            
            exposed = [i for i, b in enumerate(current_state) if b and b[-1] == '？']
            if exposed:
                print("💡 新しい '？' が見つかりました。")
                skip_input = False
                new_colors_input = []
                for i in exposed:
                    new_color = input(f"▶ ボトル {i:02d} の '？' の色が判明しました！何色ですか？ (s:スキップ, q:終了): ")
                    if new_color.lower() == 'q': return
                    if new_color.lower() == 's': 
                        skip_input = True
                        break
                    
                    if new_color in COLOR_MAP:
                        layer = len(current_state[i]) - 1
                        memory_unknowns_str[(i, layer)] = new_color
                        
                        bottle_list = list(current_state[i])
                        bottle_list[-1] = new_color
                        temp_state = list(current_state)
                        temp_state[i] = tuple(bottle_list)
                        current_state = tuple(temp_state)
                    else:
                        print(f"⚠️ 無効な色です。スキップします。")
                        skip_input = True
                        break
                        
                if not skip_input and new_colors_input:
                    continue
                elif skip_input:
                    continue
            
            has_any_unknown = any('？' in b for b in current_state)
            
            completed_counts = {}
            total_completed = 0
            for b in current_state:
                if len(b) == capacity and all(c == b[0] for c in b) and b[0] not in ('？', '封'):
                    col_id = COLOR_MAP.get(b[0], -4)
                    if col_id >= 0:
                        completed_counts[col_id] = completed_counts.get(col_id, 0) + 1
                        total_completed += 1
                        
            unmet_rules = []
            if internal_closed:
                for idx, col_id, req in internal_closed:
                    if col_id == -3:
                        if total_completed < req:
                            unmet_rules.append((idx, col_id, "無（何色でも）"))
                    else:
                        if completed_counts.get(col_id, 0) < req:
                            unmet_rules.append((idx, col_id, INV_COLOR_MAP[col_id]))

            target_colors_for_solve = set(target_colors) if target_colors else set()
            
            if target_colors:
                print(f"探索開始: [手動] 指定された色の完成を最優先で計算中...\n")
                path, next_state = solve(current_state, capacity, mode="prioritize", target_colors=target_colors_for_solve, internal_closed=internal_closed, memory_str=memory_unknowns_str, known_cups_str=known_cup_contents, simulate_unlocks=True)
            else:
                print("探索開始: [フェーズ1] 盤面の '？' の開拓を目標に計算中...")
                path, next_state = solve(current_state, capacity, mode="reveal", target_colors=set(), internal_closed=internal_closed, memory_str=memory_unknowns_str, known_cups_str=known_cup_contents, simulate_unlocks=False)
                
                if not path and unmet_rules:
                    print("\n⚠️ 現在の盤面ではこれ以上 '？' を開拓できません。")
                    print("➡️ [フェーズ2] カップを開封し、連鎖的に盤面を広げて『？』を露出させるルートを計算します。")
                    print("【 開放候補のカップ 】")
                    for rule in unmet_rules:
                        print(f"  - ボトル {rule[0]:02d} (条件: {rule[2]})")
                        
                    cup_choice = input("優先して開けたいカップの番号を入力してください (そのままEnterでソルバーが自動で最適探索): ").strip()
                    
                    target_colors_for_solve = set()
                    target_names = []
                    if cup_choice.isdigit():
                        choice_idx = int(cup_choice)
                        for rule in unmet_rules:
                            if rule[0] == choice_idx:
                                target_colors_for_solve.add(rule[1])
                                target_names.append(f"ボトル{rule[0]:02d}({rule[2]})")
                                break
                    
                    if not target_colors_for_solve:
                        target_colors_for_solve = {rule[1] for rule in unmet_rules}
                        target_names = [f"ボトル{rule[0]:02d}({rule[2]})" for rule in unmet_rules]
                        
                    mode = "unlock_reveal"
                    print(f"\n探索開始: [フェーズ2移行] {', '.join(target_names)} などの封印解除を通じて『？』を露出させるルートを計算中...\n")
                    path, next_state = solve(current_state, capacity, mode="unlock_reveal", target_colors=target_colors_for_solve, internal_closed=internal_closed, memory_str=memory_unknowns_str, known_cups_str=known_cup_contents, simulate_unlocks=True)
                    
                    if not path:
                        print("\n⚠️ どのカップを解除するルートも見つかりませんでした（または中に？がありません）。")
                        print("➡️ [フェーズ3] 可能な範囲で盤面を整理し、クリアを目指すルートを検索します...")
                        path, next_state = solve(current_state, capacity, mode="clear", target_colors=set(), internal_closed=internal_closed, memory_str=memory_unknowns_str, known_cups_str=known_cup_contents, simulate_unlocks=True)

                elif not path and not unmet_rules:
                    print("探索開始: [フェーズ3] 【全条件達成】全クリアに向けて最短ルートを計算中...\n")
                    path, next_state = solve(current_state, capacity, mode="clear", target_colors=set(), internal_closed=internal_closed, memory_str=memory_unknowns_str, known_cups_str=known_cup_contents, simulate_unlocks=True)

            if not path:
                print("\n❌ 手詰まりです。これ以上、目標を達成できる手順が見つかりません。")
                if has_any_unknown or unmet_rules:
                    print("🔄 【提案】ゲームの「リスタート」ボタンを押し、今まで判明した情報を引き継いで最初からやり直すことを推奨します。")
                    action = input("リスタートして再計算しますか？ (y:はい / n:いいえ): ").strip().lower()
                    if action == 'y': break 
                    else: next_state = current_state
                else:
                    print("⚠️ 全ての情報が判明しているのに手詰まりです。入力ミス（あるいは『封』の解除忘れ）の可能性があります。")
                    next_state = current_state
            else:
                print(f"✅ 最良 {len(path)} 手の手順が見つかりました！")
                for step_num, move in enumerate(path, 1):
                    src, dst, amount, color = move
                    print(f"  手順 {step_num}: ボトル {src:02d} から ボトル {dst:02d} へ [{color}] を {amount} つ移動")
                
                print("\n💡 【重要】手順の途中でカップが開いた場合は、そこで実行を止めて [U] コマンドで盤面を同期し、再計算させてください！")
            
            # ----------------------------------------------------
            # 拡張コマンドメニュー
            # ----------------------------------------------------
            # ★【新機能】コマンド入力をメニューループ化し、Sコマンドを追加
            while True:
                print("\n[Enter]:次へ  [R]:リスタート  [U]:実機ロック解除  [E]:編集  [P]:優先色  [S]:状況確認  [X]:データ出力  [Q]:終了")
                action = input("-> ").strip().lower()
                
                if action == 's':
                    print("\n=================================================")
                    print("【 現在の状況確認 】")
                    print("=================================================")
                    print_board(current_state, capacity, layout, internal_closed)
                    
                    if memory_unknowns_str:
                        print("💡 【 判明している『？』の記憶一覧 】")
                        memory_by_bottle = {}
                        for (b_idx, layer), color in memory_unknowns_str.items():
                            if b_idx not in memory_by_bottle:
                                memory_by_bottle[b_idx] = []
                            memory_by_bottle[b_idx].append((layer, color))
                        for b_idx in sorted(memory_by_bottle.keys()):
                            items = sorted(memory_by_bottle[b_idx])
                            mem_str = ", ".join([f"下から{l+1}層目:[{c}]" for l, c in items])
                            print(f"  ボトル {b_idx:02d} -> {mem_str}")
                    else:
                        print("💡 判明している『？』の記憶はまだありません。")
                        
                    if internal_closed:
                        print("\n🔒 【 ロック(閉)の解除待ち条件 】")
                        for idx, col_id, req in internal_closed:
                            col_name = "無（何色でも）" if col_id == -3 else INV_COLOR_MAP[col_id]
                            print(f"  ボトル {idx:02d} -> 条件: {col_name} を {req} 本完成")
                    print("=================================================\n")
                    continue
                    
                elif action == 'x':
                    export_board(base_board, layout, memory_unknowns_str, known_cup_contents)
                    continue
                    
                else:
                    break
            
            # --- 以下は状態が変わるコマンド ---
            if action == 'q': return
            elif action == 'r':
                 print("\n🔄 ゲームをリスタートし、学習した情報を引き継いで初期状態からやり直します。")
                 break 
                 
            elif action == 'u':
                print("\n【 ロック(閉)手動解除モード 】")
                
                if path:
                    print(f"\n直前に提示された手順（全 {len(path)} 手）のうち、何手目まで実行したところでカップが開きましたか？")
                    print("（まだ1手も実行していない場合は 0、最後まで実行した場合はそのままEnter）")
                    steps_str = input("実行した手数: ").strip()
                    steps_taken = 0
                    if steps_str == "":
                        steps_taken = len(path)
                    else:
                        try:
                            steps_taken = max(0, min(int(steps_str), len(path)))
                        except ValueError:
                            print("⚠️ 数字を入力してください。キャンセルします。")
                            continue
                            
                    if steps_taken > 0:
                        current_state = apply_path_to_state_str(current_state, path, steps_taken, capacity, memory_unknowns_str)
                        print(f"\n➡️ 盤面を {steps_taken} 手進めた状態に同期しました。")

                try:
                    unlock_idx = int(input("\n実機で解放されたボトルの番号を入力: "))
                    if 0 <= unlock_idx < len(current_state):
                        if any(c[0] == unlock_idx for c in internal_closed):
                            
                            if current_state[unlock_idx] and current_state[unlock_idx][0] == '封':
                                if unlock_idx in known_cup_contents:
                                    print(f"💡 ボトル {unlock_idx:02d} の中身は以前の入力により記憶されています！それを復元します。")
                                    new_bottle = known_cup_contents[unlock_idx]
                                else:
                                    print(f"\nボトル {unlock_idx:02d} のロックを完全に解除します。")
                                    print("解放されたボトルの『最初の中身』を下から順にカンマ区切りで入力してください。")
                                    print("（完全に空ボトルの場合は、何も入力せずそのままEnter）")
                                    new_contents_str = input(f"ボトル {unlock_idx:02d} の中身: ").strip()
                                    if new_contents_str:
                                        new_bottle = tuple(c.strip() for c in new_contents_str.split(',') if c.strip() in COLOR_MAP)
                                    else:
                                        new_bottle = ()
                                    known_cup_contents[unlock_idx] = new_bottle
                                
                                temp_state = list(current_state)
                                temp_state[unlock_idx] = new_bottle
                                current_state = tuple(temp_state)
                                
                                temp_base = list(base_board)
                                temp_base[unlock_idx] = new_bottle
                                base_board = tuple(temp_base)
                            else:
                                print(f"💡 ボトル {unlock_idx:02d} は既に中身が見えているため、そのままロック制約のみを解除します。")
                            
                            internal_closed = [c for c in internal_closed if c[0] != unlock_idx]
                            
                            print(f"\n➡️ ボトル {unlock_idx:02d} が正規のボトルとして解放されました！再計算します。")
                        else:
                            print("⚠️ その番号のボトルは現在ロック(閉)の条件待ちではありません。")
                    else:
                        print("⚠️ 無効な番号です。")
                except ValueError: pass
                continue

            elif action == 'e':
                try:
                    edit_idx = int(input(f"編集するボトルの番号を入力 (0〜{len(current_state)-1}): "))
                    if 0 <= edit_idx < len(current_state):
                        print("新しい中身を『下から順に』カンマ区切りで入力（空の場合はそのままEnter）")
                        new_contents_str = input(f"ボトル {edit_idx:02d} の新しい中身: ").strip()
                        if new_contents_str:
                            new_bottle = tuple(c.strip() for c in new_contents_str.split(',') if c.strip() in COLOR_MAP)
                        else:
                            new_bottle = ()
                        temp_state = list(current_state)
                        temp_state[edit_idx] = new_bottle
                        current_state = tuple(temp_state)
                    else:
                        print("⚠️ 無効な番号です。")
                except ValueError: pass
                continue
                
            elif action == 'p':
                color_str = input("\n優先するオーダーの色（空欄で解除）: ").strip()
                if color_str in COLOR_MAP and COLOR_MAP[color_str] not in (-1, -2):
                    target_colors = {COLOR_MAP[color_str]}
                else:
                    target_colors = set()
                continue 

            current_state = next_state



# ==========================================
# 実行部分（レベル108）
# ==========================================
if __name__ == "__main__":
    
    CAPACITY = 4
    LAYOUT = [3, 3, 4, 4, 4, 3, 3]

    closed = [
        (6, "無", 4), (9, "黄", 2), 
        (10, "無", 5), (13, "緑", 2), 
        (14, "無", 4), (17, "青", 2)
    ]
    
    # Xコマンドで出力された known_memory と known_cup_contents を貼り付けられます
    known_memory = {
        (0, 2): '青',
        (3, 2): '水',
        (7, 2): '黄',
        (7, 1): '黄',
        (11, 2): '青',
        (21, 2): '緑',
        (18, 2): '青',
        (11, 1): '黄',
        (7, 0): '緑',
        (21, 1): '緑',
        (21, 0): '橙',
        (4, 1): '緑',
        (8, 1): '紫',
        (15, 2): '紫',
        (15, 1): '黄',
        (15, 0): '白',
        (5, 0): '水',
        (19, 1): '橙',
        (3, 1): '黄',
        (12, 1): '青',
        (0, 1): '青',
        (11, 0): '水',
        (1, 1): '青',
        (16, 1): '水',
        (16, 0): '赤',
        (22, 1): '緑',
        (18, 1): '青',
        (22, 0): '青',
        (0, 0): '緑',
    }

    known_cup_contents = {
    }

    initial_board = (
        # --- 列 0 (左から 1 列目) ---
        ('？', '？', '？', '白'), # 00
        ('？', '？', '赤', '水'), # 01
        ('封', '封', '封', '封'), # 02

        # --- 列 1 (左から 2 列目) ---
        ('？', '？', '？', '赤'), # 03
        ('？', '？', '赤', '緑'), # 04
        ('？', '白'), # 05

        # --- 列 2 (左から 3 列目) ---
        ('封', '封', '封', '封'), # 06
        ('？', '？', '？', '黄'), # 07
        ('？', '？', '赤', '青'), # 08
        ('封', '封', '封', '封'), # 09

        # --- 列 3 (左から 4 列目) ---
        ('封', '封', '封', '封'), # 10
        ('？', '？', '？', '青'), # 11
        ('？', '？', '赤'), # 12
        ('封', '封', '封', '封'), # 13

        # --- 列 4 (左から 5 列目) ---
        ('封', '封', '封', '封'), # 14
        ('？', '？', '？', '紫'), # 15
        ('？', '？', '水', '青'), # 16
        ('封', '封', '封', '封'), # 17

        # --- 列 5 (左から 6 列目) ---
        ('？', '？', '？', '赤'), # 18
        ('？', '？', '水', '黄'), # 19
        ('？', '黄'), # 20

        # --- 列 6 (左から 7 列目) ---
        ('？', '？', '？', '白'), # 21
        ('？', '？', '赤', '水'), # 22
        ('封', '封', '封', '封'), # 23

    )

    interactive_solver(initial_board, CAPACITY, LAYOUT, closed_rules=closed, loaded_memory=known_memory, loaded_cups=known_cup_contents)

# # ==========================================
# # 実行部分（ここから下を書き換えてください）
# # ==========================================
# if __name__ == "__main__":
    
#     CAPACITY = 4
#     LAYOUT = [4, 3, 3, 2, 3, 3, 4]
    
#     known_memory = {}
#     known_cup_contents = {}
    
#     closed = [
#         (0, "緑", 1), (1, "白", 3), (2, "赤", 1), 
#         (19, "白", 5), (20, "橙", 1), (21, "紫", 1) 
#     ]

#     initial_board = (
#         # --- 列 0 (左から 1 列目) ---
#         ('？', '？', '白', '赤'), # 00
#         ('？', '？', '白', '青'), # 01
#         ('？', '白', '赤', '黄'), # 02
#         ('封', '封', '封', '封'), # 03

#         # --- 列 1 (左から 2 列目) ---
#         ('水', '緑', '緑', '黄'), # 04
#         ('青', '橙', '水', '白'), # 05
#         ('黄', '赤', '白', '黄'), # 06

#         # --- 列 2 (左から 3 列目) ---
#         ('青', '橙', '赤', '赤'), # 07
#         ('赤', '水', '紫', '紫'), # 08
#         ('橙', '橙', '紫', '赤'), # 09

#         # --- 列 3 (左から 4 列目) ---
#         ('青', '緑'), # 10
#         ('緑', '紫'), # 11

#         # --- 列 4 (左から 5 列目) ---
#         ('水', '青', '赤', '緑'), # 12
#         ('黄', '白', '黄', '白'), # 13
#         ('赤', '青', '紫', '黄'), # 14

#         # --- 列 5 (左から 6 列目) ---
#         ('白', '紫', '紫', '水'), # 15
#         ('水', '青', '橙', '青'), # 16
#         ('紫', '水', '赤', '赤'), # 17

#         # --- 列 6 (左から 7 列目) ---
#         (), # 18
#         ('？', '？', '？', '緑'), # 19
#         ('？', '？', '？', '黄'), # 20
#         ('紫', '緑', '紫', '紫'), # 21

#     )

#     interactive_solver(initial_board, CAPACITY, LAYOUT, closed_rules=closed, loaded_memory=known_memory, loaded_cups=known_cup_contents)