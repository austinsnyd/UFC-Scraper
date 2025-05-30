import sqlite3


def split_and_update(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT rowid, SIG_STR, TOTAL_STR, TD FROM Fight_Details")
    rows = cursor.fetchall()

    for row in rows:
        rowid, sig_str, total_str, td = row
        # Ensure all values are treated as strings for split operation
        sig_str = str(sig_str)
        total_str = str(total_str)
        td = str(td)

        # Process SIG_STR
        if " OF " in sig_str:
            sig_str_parts = sig_str.split(" OF ")
            sig_str_successful, sig_str_attempts = map(int, sig_str_parts)
        else:
            sig_str_successful = sig_str_attempts = 0

        # Process TOTAL_STR
        if " OF " in total_str:
            total_str_parts = total_str.split(" OF ")
            total_str_successful, total_str_attempts = map(int, total_str_parts)
        else:
            total_str_successful = total_str_attempts = 0

        # Process TD
        if " OF " in td:
            td_parts = td.split(" OF ")
            td_successful, td_attempts = map(int, td_parts)
        else:
            td_successful = td_attempts = 0

        # Execute the update query
        cursor.execute(
            """UPDATE Fight_Details SET 
            SIG_STR_SUCCESSFUL=?, SIG_STR_ATTEMPTS=?, 
            TOTAL_STR_SUCCESSFUL=?, TOTAL_STR_ATTEMPTS=?, 
            TD_SUCCESSFUL=?, TD_ATTEMPTS=? 
            WHERE rowid=?""",
            (
                sig_str_successful,
                sig_str_attempts,
                total_str_successful,
                total_str_attempts,
                td_successful,
                td_attempts,
                rowid,
            ),
        )

    conn.commit()
    conn.close()


split_and_update("UFC_Data.db")
