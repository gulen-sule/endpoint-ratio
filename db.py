import psycopg2
import uuid
import pandas as pd


class DB:
    def __init__(
        self, host="0.0.0.0", port="5443", user="postgres", password=""
    ) -> None:
        self._database = "postgres"
        self._user = user
        self._password = password
        self._table = "time_spent"
        self._conn = psycopg2.connect(
            database=self._database,
            user=self._user,
            password=self._password,
            host=host,
            port=port,
        )

    def insert_db_many(self, file_name=None, rows=None) -> (bool, str):
        cursor = self._conn.cursor()
        args_str = ",".join(
            cursor.mogrify(
                "(DEFAULT,%s,%s,%s,%s,%s,%s)",
                (
                    rows["Date"][i],
                    rows["Time"][i],
                    rows["Gate"][i],
                    rows["RegNo"][i],
                    rows["Total Spent Time(msecs)"][i],
                    rows["Image save (msecs)"][i],
                ),
            ).decode("utf-8")
            for i in range(len(rows["Date"]))
        )
        e: Exception = None
        for i in range(3):
            try:
                cursor.execute(f"INSERT INTO {self._table} VALUES " + args_str)
                self._conn.commit()
                print(
                    f"The readed csv file:{file_name} written to the database {self._database}, table {self._table}"
                )
                cursor.close()
                return (True, None)
            except Exception as exception:
                e = exception
                self._conn.rollback()

        cursor.close()
        return (False, e.__str__())

    def get_db_data(self, set=0, limit=20, required_cols={}) -> dict:
        data_dict = {col: {} for col in required_cols}
        cursor = self._conn.cursor()
        postgreSQL_select_Query = (
            f"SELECT * FROM {self._table} ORDER BY id ASC LIMIT {limit} OFFSET {set-1};"
        )

        cursor.execute(postgreSQL_select_Query)
        data = cursor.fetchall()

        for i, row in enumerate(data):
            db_index = set + i
            data_dict["Date"][db_index] = row[1].strftime("%m/%d/%Y")
            data_dict["Time"][db_index] = row[2].strftime("%H:%M")
            data_dict["Gate"][db_index] = row[3]
            data_dict["RegNo"][db_index] = row[4]
            data_dict["Total Spent Time(msecs)"][db_index] = row[5]
            data_dict["Image save (msecs)"][db_index] = row[6]

        return data_dict
