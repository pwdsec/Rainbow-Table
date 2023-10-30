### PWDSEC

import sqlite3
import hashlib
import sys
import csv

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS words_md5 (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            md5_hash TEXT NOT NULL UNIQUE
        )
        ''')
        self.conn.commit()

    def insert_word(self, word):
        md5_hash = hashlib.md5(word.encode()).hexdigest()
        try:
            self.cursor.execute('''
            INSERT INTO words_md5 (word, md5_hash) VALUES (?, ?)
            ''', (word, md5_hash))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def delete_word(self, word):
        self.cursor.execute('DELETE FROM words_md5 WHERE word = ?', (word,))
        self.conn.commit()

    def search_word(self, word):
        self.cursor.execute('SELECT md5_hash FROM words_md5 WHERE word = ?', (word,))
        return self.cursor.fetchone()

    def search_md5(self, md5_hash):
        self.cursor.execute('SELECT word FROM words_md5 WHERE md5_hash = ?', (md5_hash,))
        return self.cursor.fetchone()

    def list_all_words(self):
        self.cursor.execute('SELECT word, md5_hash FROM words_md5')
        return self.cursor.fetchall()

    def backup_database(self, backup_file):
        with sqlite3.connect(backup_file) as backup:
            self.conn.backup(backup)

    def close(self):
        self.conn.close()

    def update_word(self, old_word, new_word):
        md5_hash = hashlib.md5(new_word.encode()).hexdigest()
        self.cursor.execute('''
        UPDATE words_md5 SET word = ?, md5_hash = ? WHERE word = ?
        ''', (new_word, md5_hash, old_word))
        self.conn.commit()

    def batch_insert(self, words):
        words_with_hash = [(word, hashlib.md5(word.encode()).hexdigest()) for word in words]
        self.cursor.executemany('''
        INSERT OR IGNORE INTO words_md5 (word, md5_hash) VALUES (?, ?)
        ''', words_with_hash)
        self.conn.commit()

    def get_word_count(self):
        self.cursor.execute('SELECT COUNT(*) FROM words_md5')
        return self.cursor.fetchone()[0]

    def export_to_csv(self, csv_filename):
        with open(csv_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Word", "MD5 Hash"])
            self.cursor.execute('SELECT word, md5_hash FROM words_md5')
            writer.writerows(self.cursor.fetchall())

def process_file(db, filename):
    try:
        with open(filename, 'r') as file:
            for line in file:
                word = line.strip()
                if word:
                    db.insert_word(word)
        print(f"Processed file '{filename}' and inserted words into the database.")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except IOError:
        print(f"Error reading from '{filename}'.")

def main():
    with Database('words_md5.db') as db:
        while True:
            print("\n--- Menu ---")
            print("1. Process a file")
            print("2. Delete a word")
            print("3. Search word to get MD5 hash")
            print("4. Search MD5 hash to get word")
            print("5. List all words")
            print("6. Backup database")
            print("8. Update word")
            print("9. Display word count")
            print("10. Export to CSV")
            print("11. Exit")


            choice = input("\nEnter your choice: ")

            if choice == "1":
                filename = input("Enter the filename to process: ")
                process_file(db, filename)
            elif choice == "2":
                word = input("Enter the word to delete: ")
                db.delete_word(word)
                print(f"'{word}' deleted from the database.")
            elif choice == "3":
                word = input("Enter the word to search: ")
                md5_hash = db.search_word(word)
                if md5_hash:
                    print(f"MD5 hash for '{word}' is: {md5_hash[0]}")
                else:
                    print(f"'{word}' not found in the database.")
            elif choice == "4":
                md5_hash = input("Enter the MD5 hash to search: ")
                word = db.search_md5(md5_hash)
                if word:
                    print(f"Word for MD5 hash '{md5_hash}' is: {word[0]}")
                else:
                    print(f"MD5 hash '{md5_hash}' not found in the database.")
            elif choice == "5":
                words = db.list_all_words()
                for word, md5_hash in words:
                    print(f"{word} - {md5_hash}")
            elif choice == "6":
                backup_file = input("Enter the backup filename: ")
                db.backup_database(backup_file)
                print(f"Database backed up to '{backup_file}'")
            elif choice == "8":
                old_word = input("Enter the word to update: ")
                if db.search_word(old_word):
                    new_word = input(f"Enter the new word to replace '{old_word}': ")
                    db.update_word(old_word, new_word)
                    print(f"'{old_word}' updated to '{new_word}'.")
                else:
                    print(f"'{old_word}' not found in the database.")
            elif choice == "9":
                count = db.get_word_count()
                print(f"There are {count} words in the database.")
            elif choice == "10":
                csv_filename = input("Enter the filename to export (with .csv extension): ")
                db.export_to_csv(csv_filename)
                print(f"Data exported to '{csv_filename}'.")
            elif choice == "11":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
