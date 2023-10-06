import random


# Программно реализуйте алгоритм энтропийного сжатия с помощью конечных автоматов (Finite State Entropy Coding),
# рассмотренный на занятиях, а также соответствующий алгоритм расжатия.


def get_size_of_large_block(length: int, frequency: int) -> int:
    max_bit = 0
    while 2 ** max_bit < length / frequency:
        max_bit += 1
    return max_bit


def convert_to_binary(number: int, bits: int) -> str:
    string = ""
    while number > 0:
        string += str(number % 2)
        number //= 2
    while len(string) < bits:
        string += '0'
    return string[::-1]


def convert_from_binary(number: str) -> int:
    pow = 0
    result = 0
    for i in reversed(number):
        result += 2 ** pow * int(i)
        pow += 1
    return result


def get_frequency(message: str) -> dict[str:int]:
    result = dict()
    for letter in message:
        if letter in result.keys():
            result[letter] += 1
        else:
            result[letter] = 1

    return result


def get_amount_of_large_blocks(max_bit: int, length: int, frequency: int) -> int:
    result = int(length / (2 ** max_bit))
    if result * 2 ** max_bit == length and frequency > result:
        return result - 1
    else:
        return result


def get_amount_of_small_blocks(length: int, max_bit: int, frequency: int) -> int:
    return int((frequency - length / (2 ** max_bit)) * 2)


def get_border(amount_of_large_blocks: int, max_bit: int, length: int) -> int:
    return int(length - amount_of_large_blocks * 2 ** max_bit)


def get_info_about_letters(frequency: dict[str:int], length: int) -> dict[dict]:
    letters = dict()
    k, v = list(frequency.items())[0]
    max_bit = get_size_of_large_block(length, v)
    amount_of_large_blocks = get_amount_of_large_blocks(length=length, max_bit=max_bit, frequency=frequency[k])
    letters[k] = {"max_bit": max_bit,
                  "amount_of_large_blocks": amount_of_large_blocks,
                  "small_bit": max_bit - 1,
                  "amount_of_small_blocks": get_amount_of_small_blocks(length, max_bit, frequency[k]),
                  "border_in_bits": get_border(amount_of_large_blocks, max_bit, length),
                  "amount_of_states": frequency[k],
                  "states": list(range(0, frequency[k]))}
    # print(letters[k]["states"])
    for k, v in list(frequency.items())[1::]:
        max_bit = get_size_of_large_block(length, v)
        amount_of_large_blocks = get_amount_of_large_blocks(length=length, max_bit=max_bit, frequency=frequency[k])
        a = list(letters.values())[-1]["states"][-1] + 1
        letters[k] = {"max_bit": max_bit,
                      "amount_of_large_blocks": amount_of_large_blocks,
                      "small_bit": max_bit - 1,
                      "amount_of_small_blocks": get_amount_of_small_blocks(length, max_bit, frequency[k]),
                      "border_in_bits": get_border(amount_of_large_blocks, max_bit, length),
                      "amount_of_states": frequency[k],
                      "states": list(range(0 + a, frequency[k] + a))}
        # print(letters[k]["states"])
    return letters


def find_next_state(current_state: int, letter: str, letters: dict) -> (str, int):
    border = letters[letter]["border_in_bits"]
    if current_state < border:
        number = convert_to_binary(current_state % 2 ** letters[letter]["small_bit"], letters[letter]["small_bit"])
        state = letters[letter]["states"][(current_state / 2 ** letters[letter]["small_bit"]).__floor__()]

    else:
        number = (current_state - letters[letter]["border_in_bits"]) % 2 ** letters[letter]["max_bit"]
        number = convert_to_binary(number, letters[letter]["max_bit"])
        state = letters[letter]["states"][
            (current_state - border) // 2 ** letters[letter]["max_bit"] + letters[letter]["amount_of_small_blocks"]]

    return number, state


def get_length(frequency: dict) -> int:
    length = 0
    for k, v in frequency.items():
        length += v
    return length


def encrypt_message(frequencies, message: str) -> (str, int):
    global letters
    result = ""
    # frequency = get_frequency(message)
    frequency = update_frequencies(frequencies)
    length = get_length(frequency)
    letters = get_info_about_letters(frequency=frequency, length=length)
    current_state = random.choice(letters[message[0]]["states"])
    # current_state = letters[message[0]]["states"][0]
    # print(letters)
    for i in range(1, len(message)):
        letter = message[i]
        number, state = find_next_state(current_state, letter, letters)
        result += number
        current_state = state
        # print(number)
    return result, current_state


def find_letter(state: int) -> str:
    for k in letters.keys():
        if state in letters[k]["states"]:
            return k


def get_index_of_large_block(amount_of_large_blocks: int, letter: str, current_state: int) -> int:
    return letters[letter]["states"][-amount_of_large_blocks::].index(current_state)


def get_index_of_small_block(amount_of_small_blocks: int, letter: str, current_state: int) -> int:
    return letters[letter]["states"][:-amount_of_small_blocks + 1].index(current_state)


def find_previous_state(state: int, letter: str, encrypted_message: str) -> (int, str):
    amount_of_small_blocks = letters[letter]["amount_of_small_blocks"]
    amount_of_large_blocks = letters[letter]["amount_of_large_blocks"]
    small_bit = letters[letter]["small_bit"]
    max_bit = letters[letter]["max_bit"]
    mod = amount_of_large_blocks * 2 ** max_bit + amount_of_small_blocks * 2 ** small_bit
    border = letters[letter]["border_in_bits"]
    states = list(letters[letter]["states"])
    if state in states[-amount_of_large_blocks::]:
        number = encrypted_message[-letters[letter]["max_bit"]::]

        new_state = (border + get_index_of_large_block(amount_of_large_blocks, letter,
                                                       state) * 2 ** max_bit + convert_from_binary(
            number)) % mod
        encrypted_message = encrypted_message[:-letters[letter]["max_bit"]:]
    else:
        number = encrypted_message[-letters[letter]["small_bit"]::]

        new_state = convert_from_binary(number) + get_index_of_small_block(amount_of_small_blocks, letter,
                                                                           state) * 2 ** small_bit
        encrypted_message = encrypted_message[:-letters[letter]["small_bit"]:]
    return new_state, encrypted_message


def decrypt_message(state: int, encrypted_message: str) -> str:
    result = ""
    while encrypted_message:
        letter = find_letter(state)
        state, encrypted_message = find_previous_state(state, letter, encrypted_message)
        result += letter
    result += find_letter(state)
    return result[::-1]


def update_frequencies(frequencies: str) -> dict:
    frequencies = frequencies.strip().split(' ')
    result = dict()
    for letter in frequencies:
        frequency = int(letter.split(':')[1])
        letter = letter.split(':')[0]
        result[letter] = frequency

    return result


def main():
    #frequencies = "A:3 T:2 G:2 C:1"
    frequencies = input("Введите частоты: ")
    #message = "AATGGCAT"
    message = input("Введите сообщение, которое хотите зашифровать: ")
    encrypted_message, state = encrypt_message(frequencies, message)
    #print(letters)
    print(encrypted_message, state)
    print(decrypt_message(state, encrypted_message))


if __name__ == "__main__":
    main()
