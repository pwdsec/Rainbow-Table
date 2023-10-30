### PWDSEC

import sqlite3
import hashlib
import sys
import csv

class Database:
    HASH_FUNCTIONS = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }

    def __init__(self, db_name, hash_type="md5"):
        if hash_type not in self.HASH_FUNCTIONS:
            raise ValueError(f"Unsupported hash type: {hash_type}")

        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.hash_type = hash_type
        self.hash_function = self.HASH_FUNCTIONS[hash_type]
        self.setup_database()

    def hash_word(self, word):
        return self.hash_function(word.encode()).hexdigest()

    def setup_database(self):
        self.cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL UNIQUE
        )
        ''')
        self.conn.commit()

    def insert_word(self, word):
        word_hash = self.hash_word(word)
        try:
            self.cursor.execute('''
            INSERT INTO words (word, hash) VALUES (?, ?)
            ''', (word, word_hash))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def delete_word(self, word):
        self.cursor.execute('DELETE FROM words WHERE word = ?', (word,))
        self.conn.commit()

    def search_word(self, word):
        self.cursor.execute('SELECT hash FROM words WHERE word = ?', (word,))
        return self.cursor.fetchone()

    def search_hash(self, hash_value):
        self.cursor.execute('SELECT word FROM words WHERE hash = ?', (hash_value,))
        return self.cursor.fetchone()

    def list_all_words(self):
        self.cursor.execute('SELECT word, hash FROM words')
        return self.cursor.fetchall()

    def backup_database(self, backup_file):
        with sqlite3.connect(backup_file) as backup:
            self.conn.backup(backup)

    def close(self):
        self.conn.close()

    def update_word(self, old_word, new_word):
        new_hash = self.hash_word(new_word)
        self.cursor.execute('''
        UPDATE words SET word = ?, hash = ? WHERE word = ?
        ''', (new_word, new_hash, old_word))
        self.conn.commit()

    def batch_insert(self, words):
        words_with_hash = [(word, self.hash_word(word)) for word in words]
        self.cursor.executemany('''
        INSERT OR IGNORE INTO words (word, hash) VALUES (?, ?)
        ''', words_with_hash)
        self.conn.commit()

    def export_to_csv(self, csv_filename):
        with open(csv_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Word", f"{self.hash_type.upper()} Hash"])
            self.cursor.execute('SELECT word, hash FROM words')
            writer.writerows(self.cursor.fetchall())

    def get_word_count(self):
        self.cursor.execute('SELECT COUNT(*) FROM words')
        return self.cursor.fetchone()[0]

    def get_longest_word(self):
        self.cursor.execute('SELECT word FROM words ORDER BY LENGTH(word) DESC LIMIT 1')
        return self.cursor.fetchone()

    def get_shortest_word(self):
        self.cursor.execute('SELECT word FROM words ORDER BY LENGTH(word) ASC LIMIT 1')
        return self.cursor.fetchone()

    def get_most_recent_word(self):
        self.cursor.execute('SELECT word FROM words ORDER BY id DESC LIMIT 1')
        return self.cursor.fetchone()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

def process_file(db, filename):
    with open(filename, 'r') as file:
        words = [line.strip() for line in file if line.strip()]
        for word in words:
            db.insert_word(word)
        print(f"Processed {len(words)} words from '{filename}'.")

def display_statistics(db):
    stats = {
        "Total words": db.get_word_count(),
        "Longest word": db.get_longest_word()[0],
        "Shortest word": db.get_shortest_word()[0],
        "Most recent word": db.get_most_recent_word()[0]
    }
    print("\n--- Statistics ---")
    for key, value in stats.items():
        print(f"{key}: {value}")

def main():
    HASH_MAPPING = {
        "1": "md5",
        "2": "sha1",
        "3": "sha256",
        "4": "sha512"
    }
    
    print("Choose your hash type:")
    for key, value in HASH_MAPPING.items():
        print(f"{key}. {value.upper()}")

    hash_type = HASH_MAPPING.get(input("\nEnter your choice: "), "md5")
    print(f"Using {hash_type} for hashing.")

    MENU_OPTIONS = {
        "1": ("Process a file", process_file),
        "2": ("Delete a word", lambda db: db.delete_word(input("Enter the word to delete: "))),
        "3": ("Search word to get hash", lambda db: print(db.search_word(input("Enter the word to search: ")))),
        "4": ("Search hash to get word", lambda db: print(db.search_hash(input("Enter the hash to search: ")))),
        "5": ("List all words", lambda db: [print(f"{word} - {hash_}") for word, hash_ in db.list_all_words()]),
        "6": ("Backup database", lambda db: db.backup_database(input("Enter the backup filename: "))),
        "7": ("Batch insert words", lambda db: db.batch_insert(input("Enter words separated by space: ").split())),
        "8": ("Update word", lambda db: db.update_word(input("Enter the old word: "), input("Enter the new word: "))),
        "9": ("Display word count", lambda db: print(f"There are {db.get_word_count()} words in the database.")),
        "10": ("Export to CSV", lambda db: db.export_to_csv(input("Enter the filename to export (with .csv extension): "))),
        "12": ("Display statistics", display_statistics),
        "13": ("Exit", None)
    }

    with Database('words.db', hash_type) as db:
        while True:
            print("\n--- Menu ---")
            for key, (desc, _) in MENU_OPTIONS.items():
                print(f"{key}. {desc}")
            choice = input("\nEnter your choice: ")

            if choice == "13":
                print("Exiting...")
                break

            func = MENU_OPTIONS.get(choice, (None, None))[1]
            if func:
                func(db)
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
