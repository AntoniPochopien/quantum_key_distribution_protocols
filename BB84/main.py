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


n = 20

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

# Krok 2: Bob losuje swoje bazy i mierzy qubity, które dostał od Alice
bob_bases   = []
bob_results = []
for i in range(n):
    b_base = random.randint(0, 1)
    bob_bases.append(b_base)
    bob_results.append(measure_qubit(sent_qubits[i], b_base))

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

print("Alice bity:  ", alice_bits)
print("Alice bazy:  ", alice_bases)
print("Bob bazy:    ", bob_bases)
print("Bob wyniki:  ", bob_results)
print("Klucz Alice: ", sifted_alice)
print("Klucz Bob:   ", sifted_bob)
print("Klucze zgodne?", sifted_alice == sifted_bob)