from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
import random

def encode_qubit(bit: int, basis: int) -> QuantumCircuit:
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        # zamienia wyjście na wartość przeciwną
        qc.x(0)
    if basis == 1:
        # tworzy superpozycje
        qc.h(0)
    return qc

def measure_qubit(qc: QuantumCircuit, basis: int) -> int:
    # basis = 0 → pomiar w bazie Z (|0⟩, |1⟩)
    # basis = 1 → pomiar w bazie X (|+⟩, |−⟩)
    if basis == 1:
        # zmiana bazy X → Z (Hadamard przed pomiarem)
        qc.h(0)

    # pomiar w wybranej bazie
    qc.measure(0, 0)

    sampler = StatevectorSampler()
    result = sampler.run([qc], shots=1).result()
    counts = result[0].data.c.get_counts()
    return int(max(counts, key=counts.get))


n = 200

# Krok 1: Alice tworzy swoje bity i bazy, a następnie koduje qubity
alice_bits  = []
alice_bases = []
sent_qubits = []
for i in range(n):
    bit   = random.randint(0, 1)
    basis = random.randint(0, 1)
    alice_bits.append(bit)
    alice_bases.append(basis)
    sent_qubits.append(encode_qubit(bit, basis))

# Krok 2: Eve (podsłuch) — atak typu intercept-resend.
# Eve przechwytuje każdy qubit, mierzy go w LOSOWO wybranej przez siebie bazie
# (nie zna baz Alice), a następnie na podstawie swojego wyniku i swojej bazy
# przygotowuje NOWY qubit i wysyła go dalej do Boba.
eve_bases    = []
eve_results  = []
resent_qubits = []
for i in range(n):
    e_base = random.randint(0, 1)
    eve_bases.append(e_base)

    # pomiar przechwyconego qubita kolapsuje jego stan
    e_result = measure_qubit(sent_qubits[i], e_base)
    eve_results.append(e_result)

    # Eve odtwarza qubit zgodnie z tym, co zmierzyła, i wysyła do Boba
    resent_qubits.append(encode_qubit(e_result, e_base))

# Krok 3: Bob losuje swoje bazy i mierzy qubity, które dostał (już od Eve)
bob_bases   = []
bob_results = []
for i in range(n):
    b_base = random.randint(0, 1)
    bob_bases.append(b_base)
    bob_results.append(measure_qubit(resent_qubits[i], b_base))

# Sifting (przesiewanie): Alice i Bob publicznie wymieniają się TYLKO bazami.
# Każde z nich zna jedynie obie listy baz oraz własne bity/wyniki.

# Strona Alice: zna swoje bity oraz obie listy baz, ale NIE zna wyników Boba.
sifted_alice = []
for i in range(n):
    if alice_bases[i] == bob_bases[i]:
        sifted_alice.append(alice_bits[i])

# Strona Boba: zna swoje wyniki oraz obie listy baz, ale NIE zna bitów Alice.
sifted_bob = []
for i in range(n):
    if alice_bases[i] == bob_bases[i]:
        sifted_bob.append(bob_results[i])

# Strona Eve: podsłuchuje publiczną wymianę baz, więc przesiewa własne wyniki
# na tych samych pozycjach (zgodne bazy Alice–Bob). Tak wygląda klucz, który
# Eve myśli, że zdobyła.
sifted_eve = []
for i in range(n):
    if alice_bases[i] == bob_bases[i]:
        sifted_eve.append(eve_results[i])

# Detekcja podsłuchu: liczymy QBER (Quantum Bit Error Rate) na przesianym kluczu.
# Bez Eve QBER ≈ 0. Przy ataku intercept-resend QBER ≈ 25%.
errors = 0
for i in range(len(sifted_alice)):
    if sifted_alice[i] != sifted_bob[i]:
        errors += 1

if len(sifted_alice) > 0:
    qber = errors / len(sifted_alice)
else:
    qber = 0.0

# Ile bitów klucza Eve faktycznie odgadła poprawnie (względem klucza Alice).
eve_correct = 0
for i in range(len(sifted_alice)):
    if sifted_alice[i] == sifted_eve[i]:
        eve_correct += 1

if len(sifted_alice) > 0:
    eve_knowledge = eve_correct / len(sifted_alice)
else:
    eve_knowledge = 0.0

print("Alice bity:  ", alice_bits)
print("Alice bazy:  ", alice_bases)
print("Eve bazy:    ", eve_bases)
print("Eve wyniki:  ", eve_results)
print("Bob bazy:    ", bob_bases)
print("Bob wyniki:  ", bob_results)
print("Klucz Alice: ", sifted_alice)
print("Klucz Bob:   ", sifted_bob)
print("Klucz Eve:   ", sifted_eve)
print("Klucze zgodne?", sifted_alice == sifted_bob)
print(f"QBER:         {qber:.0%} ({errors}/{len(sifted_alice)} błędów)")
print(f"Wiedza Eve:   {eve_knowledge:.0%} ({eve_correct}/{len(sifted_alice)} bitów trafionych)")

# Zamienia listę bitów (0/1) na listę bajtów (po 8 bitów na znak)
def bits_to_key_bytes(bits: list, length: int) -> list:
    if len(bits) < length * 8:
        raise ValueError(
            f"Za krótki klucz: potrzeba {length * 8} bitów, jest {len(bits)}. Zwiększ n."
        )
    key_bytes = []
    for c in range(length):
        byte = 0
        for b in range(8):
            byte = (byte << 1) | bits[c * 8 + b]
        key_bytes.append(byte)
    return key_bytes


alice_message = "Hello, Bob!"

# Klucz w postaci bajtów (osobno dla Alice i Boba z ich przesianych bitów)
alice_key = bits_to_key_bytes(sifted_alice, len(alice_message))
bob_key = bits_to_key_bytes(sifted_bob, len(alice_message))
eve_key = bits_to_key_bytes(sifted_eve, len(alice_message))

# Alice szyfruje wiadomość kluczem (XOR na wartości liczbowej znaku)
alice_cipher = []
for i in range(len(alice_message)):
    alice_cipher.append(ord(alice_message[i]) ^ alice_key[i])

print("Alice zaszyfrowana wiadomość: ", alice_cipher)

# Eve deszyfruje wiadomość kluczem
eve_message = ""
for i in range(len(alice_cipher)):
    eve_message += chr(alice_cipher[i] ^ eve_key[i])

print("Eve deszyfrowana wiadomość: ", eve_message)

# Bob deszyfruje wiadomość kluczem
bob_message = ""
for i in range(len(alice_cipher)):
    bob_message += chr(alice_cipher[i] ^ bob_key[i])

print("Bob deszyfrowana wiadomość: ", bob_message)

