import os
import sys
import re
import argparse

'''
16進文字列かチェックする
'''
def is_hexstr(val):
    try:
        int(val, 16)
        return True
    except ValueError as e:
        return False

'''
チェックサム付きの16進ダンプ
    data:       データのリスト
    offset:     表示開始位置の先頭からのバイト数
    adr:        表示アドレス
    x_bytes:    X方向のバイト数
    y_bytes:    Y方向のバイト数
'''
def print_hexdump(data, offset=0, adr=0):
    x_bytes = 16
    y_bytes = 16
    print('Add  ', end='')
    for x in range(x_bytes):
        print('+{:X}'.format(x), end=' ')
    print('Sum')
    y_sum = [0] * (x_bytes + 1)
    for y in range(y_bytes):
        x_sum = 0
        print('{:04X}'.format(adr), end=' ')
        for x in range(x_bytes):
            d = data[y * x_bytes + x + offset]
            print('{:02X}'.format(d), end=' ')
            x_sum    += d
            y_sum[x] += d
        print('{:02X}'.format(x_sum & 0xff))
        y_sum[x_bytes] += x_sum
        adr += x_bytes
    print('Sum ', end=' ')
    for x in range(x_bytes):
        print('{:02X}'.format(y_sum[x] & 0xff), end=' ')
    print('{:02X}'.format(y_sum[x_bytes] & 0xff))
    print('')

'''
バイナリ変換
    file:   テキストファイル

    以下のフォーマットのテキストファイルを読んで、バイナリのリストとベースアドレスを返す。
    チェックサムの計算も行い、一致しない場合はエラーを表示する。
    1ブロック分のフォーマット:
        Add  +0 +1 +2 +3 +4 +5 +6 +7 +8 +9 +A +B +C +D +E +F Sum
        0100 30 17 0E 2D 35 01 4E 4F 4C 3B 11 3B 13 09 07 2E 79
        0110 25 3F 4B 56 04 10 60 1A 29 1E 2B 1F 5E 53 60 18 4D
        0120 52 61 2C 2B 46 4C 1C 13 5A 42 01 54 59 14 2B 36 8A
        0130 50 37 49 3D 4C 1F 34 1F 3B 2D 5C 44 1F 10 2B 3A 67
        0140 26 14 06 45 0B 28 4A 23 56 3E 13 03 51 4E 0B 39 B2
        0150 58 0A 06 2D 5E 0E 3A 30 29 5E 2B 0A 45 27 43 03 D9
        0160 50 35 35 3D 34 26 42 35 2C 3C 4C 07 41 4A 1A 5C 84
        0170 51 13 4A 51 60 58 4B 52 18 17 41 4F 44 3A 4E 4D 2C
        0180 5F 3E 5C 04 58 32 01 24 0F 04 2C 2C 11 63 54 2A 09
        0190 28 09 43 4C 2F 36 0A 1C 46 3B 30 29 02 1B 25 18 7F
        01A0 56 32 4A 0A 23 18 28 5E 64 5D 64 32 1F 06 62 41 BC
        01B0 2D 42 1E 26 58 0E 30 5F 2C 1C 3C 3D 04 0F 04 3B BB
        01C0 5D 18 3B 04 05 30 42 48 11 32 02 4E 3B 36 45 55 11
        01D0 08 03 12 1A 64 62 64 48 06 3A 3A 53 1B 0A 4E 2A 13
        01E0 41 41 0F 1A 1E 3D 45 47 5B 56 41 33 06 2A 22 57 60
        01F0 24 04 51 2F 43 30 62 14 28 1C 47 4A 27 0D 4D 3C 23
        Sum  EA 6F 0D D2 94 BD BF 5D 4C 4D 24 37 BD 83 54 6B 98
'''
def read_dumptext(file):
    IsBaseAdr = True
    base_adr  = 0
    block_adr = 0
    data = []
    x_bytes = 16
    y_bytes = 16
    y_sum  = [0] * x_bytes
    xy_sum = 0
    yyy = 0
    with open(file, 'r', newline='') as f:
        for line in f:
            # 改行削除し、スペースまたは':'でトークン分割後、大文字変換
            token_list = [token.upper() for token in 
                          list(filter(None, re.split('[ :]', line.strip('\n'))))]

            if len(token_list) == 0:
                # 空行を検出(skip)
                continue
            elif 'ADD' in token_list[0] or '+' in token_list[0]:
                # 先頭のトークンに'ADD'または'+'が含まれる行(skip)を検出
                yyy = 0
                continue
            elif token_list[0] == 'SUM':
                # チェックサム行を検出
                if yyy != y_bytes:
                    print("Block address : 0x{:X}".format(block_adr))
                    print("Number of data lines is {}. It should be {}.".format(yyy, y_bytes))
                    sys.exit()
                # トークンの中身が16進数かチェック
                for x in range(1, x_bytes + 2):
                    if is_hexstr(token_list[x]) == False:
                        print("Block address : 0x{:X}".format(block_adr))
                        if x == x_bytes + 1:
                            print("Invalid Checksum : ", token_list[x])
                        else:
                            print("Invalid data : +{:X} {}".format(x - 1, token_list[x]))
                        print(token_list)
                        sys.exit()
                # Y方向のチェックサム確認
                for x in range(x_bytes):
                    if (y_sum[x] & 0xff) != int(token_list[x + 1], base=16):
                        print("Block address : 0x{:X}".format(block_adr))
                        print('Y  Checksum error : +{:X} {:02X} should be {}'.format(x, y_sum[x] & 0xff, token_list[x + 1]))
                        print(token_list)
                        sys.exit()
                # 総チェックサムの確認
                if (xy_sum & 0xff) != int(token_list[x_bytes + 1], base=16):
                    print("Block address : 0x{:X}".format(block_adr))
                    print('XY Checksum error : {:02X} should be {}'.format(xy_sum & 0xff, token_list[x_bytes + 1]))
                # チェックサムのリセット
                y_sum  = [0] * x_bytes
                xy_sum = 0
                yyy = 0
            elif len(token_list) != x_bytes + 2:
                # データ行っぽいが期待するトークンと異なる行を検出
                print('Tokenize error: line=', yyy)
                print(token_list)
                sys.exit()
                continue
            else:
                # フォーマットが正しいデータ行を検出
                # トークンの中身が16進数かチェック
                for x in range(x_bytes + 2):
                    if is_hexstr(token_list[x]) == False:
                        if x == 0:
                            print("Invalid address : ", token_list[x])
                        elif x == x_bytes + 1:
                            print("Invalid Checksum : ", token_list[x])
                        else:
                            print("Invalid data : +{:X} {}".format(x - 1, token_list[x]))
                        print(token_list)
                        sys.exit()
                # 先頭アドレスの保存
                if IsBaseAdr == True:
                    IsBaseAdr = False
                    base_adr = int(token_list[0], base=16)
                # ブロックアドレスの保存
                if yyy == 0:
                    block_adr = int(token_list[0], base=16)
                # 1行分のバイナリ変換
                x_sum = 0
                for x in range(x_bytes):
                    d = int(token_list[x + 1], base=16)
                    data += [d]
                    x_sum    += d       # X方向のチェックサム計算
                    y_sum[x] += d       # Y方向のチェックサム計算
                # X方向のチェックサム確認
                if (x_sum & 0xff) != int(token_list[x_bytes + 1], base=16):
                    print("X  Checksum error : ", token_list)
                # 総チェックサム計算
                xy_sum += x_sum
                # Y方向のカウント
                yyy += 1
    return data, base_adr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='16進ダンプコンバータ')
    parser.add_argument('in_file',          help='入力テキストファイル名')
    parser.add_argument('-o', '--out_file', help='バイナリ出力ファイル名')
    parser.add_argument('-d', '--dump',     help='16進ダンプ出力', action='store_true')
    args = parser.parse_args()

    # in_file
    if os.path.isfile(args.in_file) == False:
        print('File not found:', args.in_file)
        sys.exit()
    else:
        data, base_adr = read_dumptext(args.in_file)
        size = len(data)

    # --out_file
    if args.out_file != None:
        with open(args.out_file, 'wb') as f:
            f.write(bytearray(data[:size]))

    # --dump
    if args.dump == True:
        for offset in range(0, size, 256):
            print_hexdump(data, offset, adr = base_adr)
        print('Data size=0x{:X}'.format(size))
