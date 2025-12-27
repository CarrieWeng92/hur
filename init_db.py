import os
import psycopg2

# 1. 取得 Render 環境變數中的資料庫連線網址
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("錯誤：找不到 DATABASE_URL，請確認你是在 Render 環境執行，或已設定環境變數。")
    exit()

# 2. 連線資料庫
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

try:
    print("正在建立資料表 hur_members...")
    
    # 建立資料表指令
    create_table_query = """
    CREATE TABLE IF NOT EXISTS hur_members (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        intro TEXT
    );
    """
    cursor.execute(create_table_query)
    
    # 3. 檢查裡面是不是空的，如果是空的才寫入資料 (避免重複寫入)
    cursor.execute("SELECT COUNT(*) FROM hur_members;")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("資料表為空，正在寫入 HUR+ 成員資料...")
        
        # 準備要寫入的資料 (請確認這裡的圖片檔名跟你實際存的一樣)
        members_data = [
            ('利善榛', 'cindy.png', '1995年3月18日\nLeader、Sub-Vocal、Visual'),
            ('裴頡', 'jasmine.png', '1997年3月13日\nLead Vocal、Center'),
            ('C.HOLLY', 'cholly.png', '1998年3月24日\nMain Rapper、Lead Dancer'),
            ('連穎', 'erin.png', '1999年4月27日\nMain Dancer、Sub-Vocal'),
            ('巴倫月', 'sizi.png', '1999年5月12日\nMain Vocal'),
            ('席子淇', 'jennifer.png', '2000年8月15日\nSub-Vocal、Sub-Dancer'),
            ('佟凱玲', 'shannon.png', '1999年1月14日\nSub-Vocal、Sub-Dancer'),
            ('林詩雅', 'grace.png', '1999年1月13日\nSub-Vocal、Sub-Dancer'),
            ('香蘭', 'lanlan.png', '2008年3月13日\nSub-Vocal、Maknae')
        ]
        
        insert_query = "INSERT INTO hur_members (name, filename, intro) VALUES (%s, %s, %s)"
        cursor.executemany(insert_query, members_data)
        print(f"成功寫入 {len(members_data)} 筆成員資料！")
    else:
        print(f"資料表內已有 {count} 筆資料，跳過寫入步驟。")

    # 4. 提交變更
    conn.commit()
    print("資料庫初始化完成！")

except Exception as e:
    print("發生錯誤：", e)
    conn.rollback()

finally:
    cursor.close()
    conn.close()