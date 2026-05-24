import heapq
from itertools import count
import sys

# 【内部計算用の色マッピング】
COLOR_MAP = {'？': -1, '封': -2, '赤': 0, '青': 1, '水': 2, '緑': 3, '黄': 4, '橙': 5, '紫': 6, '白': 7}
INV_COLOR_MAP = {v: k for k, v in COLOR_MAP.items()}

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

def get_possible_moves(state, capacity, target_colors=None):
    if target_colors is None: target_colors = set()
    next_states = []
    
    for i in range(len(state)):
        src = state[i]
        if not src: continue
        if src[0] == -2: continue 
        if len(src) == capacity and all(c == src[0] for c in src): continue
            
        src_color, src_count = get_top_info(src)
        if src_color in (-1, -2) or src_count == 0: continue

        for j in range(len(state)):
            if i == j: continue
            dst = state[j]
            if dst and dst[0] == -2: continue 
            if len(dst) == capacity: continue
            if not dst and src_count == len(src): continue
            
            dst_color, _ = get_top_info(dst)
            if not dst or dst_color == src_color:
                space = capacity - len(dst)
                move_amount = min(src_count, space)
                
                new_src = src[:-move_amount] if move_amount < len(src) else ()
                new_dst = dst + (src_color,) * move_amount
                
                new_state = list(state)
                new_state[i] = new_src
                new_state[j] = new_dst
                
                action_cost = 10 
                
                a_bottle = new_state[i]
                if a_bottle and a_bottle[-1] not in (-1, -2):
                    a_top = a_bottle[-1]
                    has_empty = any(not b for b in new_state)
                    has_match = any(k != i and b and b[0] != -2 and b[-1] == a_top for k, b in enumerate(new_state))
                    if not has_empty and not has_match:
                        action_cost += 100 
                
                if src_color in target_colors:
                    if len(new_dst) == capacity and all(c == src_color for c in new_dst):
                        action_cost = 0  
                    else:
                        action_cost = 2  
                        
                move_info = (i, j, move_amount, INV_COLOR_MAP[src_color])
                next_states.append((tuple(new_state), move_info, action_cost))
                
    return next_states

def is_cleared(state, capacity):
    for b in state:
        if not b: continue
        if b[0] == -2: continue
        if len(b) != capacity or len(set(b)) != 1: return False
    return True

def get_exposed_unknowns(state):
    return [i for i, b in enumerate(state) if b and b[-1] == -1]

def count_completed(state, target_id, capacity):
    if target_id is None: return 0
    return sum(1 for b in state if len(b) == capacity and all(c == target_id for c in b))

def solve(initial_str_state, capacity, mode="clear", target_colors=None):
    int_state = to_int_state(initial_str_state)
    tie_breaker = count()
    queue = [(0, next(tie_breaker), int_state, [])]
    visited = {int_state: 0}
    
    initial_unknowns = len(get_exposed_unknowns(int_state))
    target_id = list(target_colors)[0] if target_colors else None
    initial_completed = count_completed(int_state, target_id, capacity)
    iteration_count = 0 

    while queue:
        iteration_count += 1
        current_cost, _, state, path = heapq.heappop(queue)

        if iteration_count % 5000 == 0:
            print(f"\r⏳ 計算中... (探索済みパターン: {len(visited):,} | 現在の探索深さ: {current_cost})", end="", flush=True)

        if mode == "prioritize" and target_id is not None:
            if count_completed(state, target_id, capacity) > initial_completed:
                if iteration_count >= 5000: print()
                return path, to_str_state(state)
        elif mode == "clear" and is_cleared(state, capacity):
            if iteration_count >= 5000: print()
            return path, to_str_state(state)
        elif mode == "reveal":
            if len(get_exposed_unknowns(state)) > initial_unknowns:
                if iteration_count >= 5000: print()
                return path, to_str_state(state)

        for next_state, move_info, action_cost in get_possible_moves(state, capacity, target_colors):
            new_cost = current_cost + action_cost
            if next_state not in visited or new_cost < visited[next_state]:
                visited[next_state] = new_cost
                heapq.heappush(queue, (new_cost, next(tie_breaker), next_state, path + [move_info]))

    if iteration_count >= 5000: print()
    return None, None

def print_board(state, capacity, layout):
    """
    レイアウト表示のズレを修正（視覚的幅を7文字分に統一）
    """
    max_rows = max(layout) if layout else 0
    num_cols = len(layout)
    
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
                num_str += f"  {idx:02d}   "
            else:
                bottom_str += "       "
                num_str += "       "
        print(bottom_str)
        print(num_str)
        print() 
        
    print("="*(num_cols * 7) + "\n")

def update_master_board(master_board, current_state, exposed_indexes, new_colors):
    new_master = list(master_board)
    for i, bottle_idx in enumerate(exposed_indexes):
        current_len = len(current_state[bottle_idx])
        master_bottle = list(new_master[bottle_idx])
        if 0 <= current_len - 1 < len(master_bottle):
            master_bottle[current_len - 1] = new_colors[i]
            new_master[bottle_idx] = tuple(master_bottle)
    return tuple(new_master)

def export_board(board, layout):
    """
    スクリプトにそのまま貼り付けられるクリーンな形式で出力
    """
    print("\n" + "★"*60)
    print("【 現在の盤面データ (コピペ保存用) 】")
    print("以下の `initial_board = (...)` のブロックを全てコピーし、")
    print("スクリプト下部の同じ箇所を上書きペーストしてください。")
    print("★"*60)
    
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

def interactive_solver(master_initial_board, capacity, layout):
    if sum(layout) != len(master_initial_board):
        print(f"\n⚠️ 【警告】 LAYOUTの合計({sum(layout)}本)と、initial_boardのボトル数({len(master_initial_board)}本)が一致していません！\n")

    base_board = master_initial_board
    target_colors = set()
    
    while True:
        current_state = base_board
        print("\n" + "★"*50)
        print("【 新しい探索（またはリスタート）を開始します 】")
        print("★"*50)
        
        while True:
            print_board(current_state, capacity, layout)
            
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
                        new_colors_input.append(new_color)
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
                    base_board = update_master_board(base_board, current_state, exposed, new_colors_input)
                    continue
                elif skip_input:
                    continue
                
            has_any_unknown = any('？' in b for b in current_state)
            
            if target_colors:
                mode = "prioritize"
                target_name = INV_COLOR_MAP[list(target_colors)[0]]
                print(f"探索開始: [{target_name}] の完成を最優先で計算中...\n")
            elif has_any_unknown:
                mode = "reveal"
                print("探索開始: '？' の開拓を目標に計算中...\n")
            else:
                mode = "clear"
                print("探索開始: 【全情報判明】全クリアに向けて最短ルートを計算中...\n")
            
            path, next_state = solve(current_state, capacity, mode, target_colors)
            
            if not path and mode == "prioritize":
                print(f"⚠️ 現在の盤面では [{target_name}] を完成できません。先に '？' を開拓します。")
                mode = "reveal" if has_any_unknown else "clear"
                path, next_state = solve(current_state, capacity, mode, target_colors)

            if not path:
                print("\n❌ 手詰まりです。これ以上、目標を達成できる手順が見つかりません。")
                if has_any_unknown:
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
                
                if mode == "clear" and is_cleared(to_int_state(next_state), capacity):
                    print("\n🎉 全てのボトルが完成するルートです！")
            
            # ----------------------------------------------------
            # 拡張コマンドメニュー
            # ----------------------------------------------------
            print("\n[Enter]:次へ  [R]:リスタート  [U]:ロック解除  [E]:編集  [P]:優先色  [X]:盤面データ出力  [Q]:終了")
            action = input("-> ").strip().lower()
            
            if action == 'q': return
                
            elif action == 'r':
                 print("\n🔄 ゲームをリスタートし、学習した情報を引き継いで初期状態からやり直します。")
                 break 
            
            elif action == 'x':
                export_board(base_board, layout)
                continue
                 
            elif action == 'u':
                print("\n【 ロック(封)解除モード 】")
                try:
                    unlock_idx = int(input("カップや広告が消えて解放されたボトルの番号を入力: "))
                    if 0 <= unlock_idx < len(current_state) and current_state[unlock_idx] and current_state[unlock_idx][0] == '封':
                        print(f"\nボトル {unlock_idx:02d} のロックを解除します。")
                        print("解放されたボトルの『最初の中身』を下から順にカンマ区切りで入力してください。")
                        print("（完全に空ボトルの場合は、何も入力せずそのままEnter）")
                        new_contents_str = input(f"ボトル {unlock_idx:02d} の中身: ").strip()
                        if new_contents_str:
                            new_bottle = tuple(c.strip() for c in new_contents_str.split(',') if c.strip() in COLOR_MAP)
                        else:
                            new_bottle = ()
                        
                        temp_state = list(current_state)
                        temp_state[unlock_idx] = new_bottle
                        current_state = tuple(temp_state)
                        
                        temp_base = list(base_board)
                        temp_base[unlock_idx] = new_bottle
                        base_board = tuple(temp_base)
                        print(f"\n➡️ ボトル {unlock_idx:02d} を解放しました！")
                    else:
                        print("⚠️ その番号は『封』状態ではありません。")
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
# 実行部分（レベル67を想定した設定例）
# ==========================================
if __name__ == "__main__":
    
    CAPACITY = 4
    LAYOUT = [4, 3, 3, 4, 3, 3, 4]
    closed = [(3,"緑", 2), (11,"水",1), (15,"無",3)]

    initial_board = (
        # --- 列 0 (左から 1 列目) ---
        ('赤', '緑', '青', '白'), # 00
        ('橙', '紫', '赤'), # 01
        ('？', '水', '紫'), # 02
        ('封', '封', '封', '封'), # 03

        # --- 列 1 (左から 2 列目) ---
        ('緑', '紫', '赤', '白'), # 04
        ('橙', '白', '橙', '緑'), # 05
        ('黄', '緑', '青'), # 06

        # --- 列 2 (左から 3 列目) ---
        ('青', '青', '赤', '白'), # 07
        ('封', '封', '封', '封'), # 08
        ('青', '水', '赤'), # 09

        # --- 列 3 (左から 4 列目) ---
        ('水', '赤', '赤', '橙'), # 10
        ('？', '水', '橙', '緑'), # 11
        ('封', '封', '封', '封'), # 12
        ('？', '？', '緑', '水'), # 13

        # --- 列 4 (左から 5 列目) ---
        ('緑', '緑', '青', '白'), # 14
        ('封', '封', '封', '封'), # 15
        ('赤', '緑', '青'), # 16

        # --- 列 5 (左から 6 列目) ---
        ('？', '青', '黄', '白'), # 17
        ('？', '？', '白', '紫'), # 18
        ('水', '青', '水'), # 19

        # --- 列 6 (左から 7 列目) ---
        ('？', '紫', '緑', '紫'), # 20
        ('？', '橙', '紫'), # 21
        ('？', '黄', '緑'), # 22
        ('封', '封', '封', '封'), # 23
    )

    interactive_solver(initial_board, CAPACITY, LAYOUT)