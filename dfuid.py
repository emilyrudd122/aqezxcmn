"""
    lolz.guru df_uid fetcher
    made by t.me/opcod3 (t.me/opcodedev)
"""

import re
from typing import Dict, List, Optional
from Crypto.Cipher import AES
import requests
import aiohttp
import asyncio

class DfUid:
    def __init__(self, user_agent: str, proxies: Optional[Dict[str, str]] = None) -> None:
        self.__proxies = proxies
        self.__ua = user_agent
        print(proxies)
        
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': self.__ua
        }
        self.session.proxies = self.__proxies
    
    @staticmethod
    def to_numbers(string: str) -> List[int]: return [int(el, 16) for el in re.findall(r"(..)", string)]
    
    @staticmethod
    def from_char_code(char_list: list) -> str: return ''.join(map(chr, char_list))
    
    @staticmethod
    def to_int(l: list) -> List[int]: return list(map(int, l))

    @staticmethod
    def to_hex(char_list: list) -> str:
        result = ""
        for i in char_list:
            result += ("0" if 16 > i else "") + hex(i).strip("0x")
        return result.lower()

    @staticmethod
    def convert_list_to_bytes(nums: list) -> bytes:
        Bytes = b""
        for i in nums:
            b = i.to_bytes((i.bit_length() + 7) // 8, 'big')
            Bytes += b
        return Bytes

    @staticmethod
    def decrypt(data: bytes, key: bytes, iv: bytes) -> str:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = cipher.decrypt(data)
        return bytearray(data).hex()
    
    def fetch(self):
        try:
            raw = self.session.get('https://lolz.guru/market').text
        except asyncio.exceptions.TimeoutError:
            print("timeout error")
            # await asyncio.sleep(4)
            return 0
        except aiohttp.client_exceptions.ClientConnectorError:
            print("mamu ebal")
            return 0
        try:
            data_raw = re.findall(r'toNumbers\("(.+)"\)', raw)[0]
            key_raw, iv_raw = re.findall(r'toNumbers\(String.fromCharCode\((.*?)\)\)', raw)
            
            data = self.convert_list_to_bytes(self.to_numbers(data_raw))
            iv = self.convert_list_to_bytes(self.to_numbers(self.from_char_code(self.to_int(iv_raw.split(",")))))
            key = self.convert_list_to_bytes(self.to_numbers(self.from_char_code(self.to_int(key_raw.split(",")))))
            
            df_id = self.decrypt(data, key, iv)
            return df_id
        except Exception as e:
            print(f"ошибка при парсе dfuid {e}")
            return 0
    
    
if __name__ == "__main__":
    async def main():
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        df_id_fetcher = DfUid(
            ua,
            f"http://168.81.254.44:3128"
        )
        df_uid = await df_id_fetcher.fetch()
        print('df uid:', df_uid)
        # print(df_id_fetcher.session.get('https://lolz.guru/', headers={'user-agent': ua},
        #                                 cookies={'df_uid': df_uid}).text[:100])

    asyncio.run(main())
