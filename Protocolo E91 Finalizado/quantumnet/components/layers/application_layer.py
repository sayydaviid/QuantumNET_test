import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Qubit, Logger, Epr
from random import uniform, choice
import random

class ApplicationLayer:
    def __init__(self, network, network_layer, link_layer, physical_layer):
        self._network = network
        self._network_layer = network_layer
        self._link_layer = link_layer
        self._physical_layer = physical_layer
        self.logger = Logger.get_instance()
    
    def prepara_qubits_e91(self, key, bases):
        pairs = []
        for bit, base in zip(key, bases):
            qubit = Qubit(qubit_id=random.randint(0, 1000))
            if bit == 1:
                qubit.apply_x()
            if base == 1:
                qubit.apply_hadamard()
            pairs.append(qubit)
        return pairs
    
    def apply_bases_and_measure_e91(self, qubits, bases):
        results = []
        for qubit, base in zip(qubits, bases):
            if base == 1:
                qubit.apply_hadamard()
            measurement = qubit.measure()
            results.append(measurement)
        return results
    
    def qkd_e91_protocol(self, alice_id, bob_id):
        alice = self._network.hosts[alice_id]
        bob = self._network.hosts[bob_id]
        
        # Step 1: Alice prepares qubits
        key = [random.choice([0, 1]) for _ in range(10)]
        bases_alice = [random.choice([0, 1]) for _ in range(10)]
        qubits = self.prepara_qubits_e91(key, bases_alice)
        
        # Step 2: Bob chooses random bases and measures qubits
        bases_bob = [random.choice([0, 1]) for _ in range(10)]
        results_bob = self.apply_bases_and_measure_e91(qubits, bases_bob)
        
        # Step 3: Alice and Bob share their bases
        # In a real scenario, this would be done through classical communication
        common_indices = [i for i in range(len(bases_alice)) if bases_alice[i] == bases_bob[i]]
        
        if not common_indices:
            self.logger.log("Nenhuma base em comum, tentativa novamente.")
            return False
        
        # Step 4: Extract the key based on common bases
        shared_key_alice = [key[i] for i in common_indices]
        shared_key_bob = [results_bob[i] for i in common_indices]
        
        if shared_key_alice == shared_key_bob:
            self.logger.log(f"Protocolo E91 bem-sucedido. Chave compartilhada: {shared_key_alice}")
            return True
        else:
            self.logger.log("As chaves não coincidem. Tentativa novamente.")
            return False