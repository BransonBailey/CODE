from neuprint import Client
import os

c = Client('neuprint.janelia.org', dataset='male-cns:v1.0', token=os.environ['NEUPRINT_APPLICATION_CREDENTIALS'])
c.fetch_version()

from neuprint import fetch_neurons
neurons, sysdist = fetch_neurons("DNge104")

from neuprint import fetch_adjacencies
outgoing_edges, neuron_info = fetch_adjacencies("DNge104")
incoming_edges, neuron_info2 = fetch_adjacencies(None, "DNge104")
