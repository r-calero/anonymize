import os
import re
import base64
import hashlib
import pandas as pd
from enum import Enum
from cryptography.fernet import Fernet

# define an enumeration for data types
class DataType(Enum):
    EMAIL = 'email'
    ADDRESS = 'address'
    BIRTHDAY = 'birthday'
    PAYMENT_CARD = 'card'
  
# Private obfuscation functions for email, address and payment card
def __obfuscate_email(email):
    user, domain = email.split('@')
    obfuscated_user = user[:2] + '*' * (len(user) - 2)
    return f"{obfuscated_user}@{domain}"

def __obfuscate_birthday(birthday):
    return f"{birthday[:4]}-**-**"

def __obfuscate_payment_card(card_number):
    digits = re.sub(r'\D', '', card_number)
    return f"**** **** **** {digits[-4:]}"

def __obfuscate_address(address):
    location_pattern = r'(,\s[A-Z]{2,4}\s\d{5}(?:-\d{4})*)$'
    match = re.search(location_pattern, address, re.IGNORECASE)
    return f"[ANONYMIZED_ADDRESS] {match.group(1)}" if match else "[ANONYMIZED_ADDRESS]"

# Function to load data from a CSV file with error handling
def load_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print("Error: The file is empty.")
        return None
    except pd.errors.ParserError:
        print("Error: There was a parsing error while reading the file.")
        return None

# Function to generate a random salt
def generate_salt(length=16):
    salt = base64.b64encode(os.urandom(length)).decode('utf-8')
    return salt

# Function to generate a hash key using SHA-256 with salt
def generate_hash_key(data, salt):
    salted_data = f"{data}{salt}".encode('utf-8')
    hashed = hashlib.sha256(salted_data).hexdigest()
    return hashed

# Function to cipher data using Fernet symmetric encryption
def cipher_data(data, key):
    # Convert the hex key to bytes and then to a Fernet-compatible key
    key_bytes = bytes.fromhex(key)
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    # cipher the data using Fernet
    cipher = Fernet(fernet_key)
    encrypted_data = cipher.encrypt(data.encode())
    return encrypted_data

# Function to decipher data using Fernet symmetric encryption
def decipher_data(data, key):
    # Convert the hex key to bytes and then to a Fernet-compatible key
    key_bytes = bytes.fromhex(key)
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    # decipher the data using Fernet
    cipher = Fernet(fernet_key)
    decrypted_data = cipher.decrypt(data)
    return decrypted_data.decode()

# Function to obfuscate data based on its type
def obfuscate_data(data, type: DataType):
    if type == DataType.EMAIL:
        return __obfuscate_email(data)
    elif type == DataType.BIRTHDAY:
        return __obfuscate_birthday(data)
    elif type == DataType.ADDRESS:
        return __obfuscate_address(data)
    elif type == DataType.PAYMENT_CARD:
        return __obfuscate_payment_card(data)
    else:
        raise ValueError("Data type not supported for obfuscation.")

# Main function to load data, generate salts and hash keys, and anonymize data
def main():
    file_path = 'data/db_clientes.csv'  # Replace with your CSV file path
    data = load_data(file_path)
    reference_data = []
    anonymized_data = []
    
    if data is not None:
        print("Data loaded successfully:")
        for index, row in data.iterrows():
            # generate reference data for deciphering personal data if needed
            item = {'Cliente_ID': row['Cliente_ID'], 'salt': generate_salt()}
            reference_data.append(item.copy())
            # generate hash key for anonymization
            hash_key = generate_hash_key(row['Cliente_ID'], item['salt'])
            # anonymize personal data with name encrypted and other fields obfuscated
            item['Nombre_Completo'] = cipher_data(row['Nombre_Completo'], hash_key).decode('utf-8')
            item['Fecha_Nacimiento'] = obfuscate_data(row['Fecha_Nacimiento'], DataType.BIRTHDAY)
            item['Correo_Electronico'] = obfuscate_data(row['Correo_Electronico'], DataType.EMAIL)
            item['Direccion'] = obfuscate_data(row['Direccion'], DataType.ADDRESS)
            item['Numero_Tarjeta'] = obfuscate_data(row['Numero_Tarjeta'], DataType.PAYMENT_CARD)
            item['Segmento'] = row['Segmento']
            del item['salt']  # Remove salt from the anonymized data for security
            anonymized_data.append(item)

        pd.DataFrame(reference_data).to_csv('data/reference_data.csv', index=False)
        pd.DataFrame(anonymized_data).to_csv('data/anonymized_data.csv', index=False)
        print("Anonymized data and reference data have been saved to CSV files.")
    else:
        print("Failed to load data.")
        
if __name__ == "__main__":
    main()