import numpy as np
import os
import sys
sys.path.append(os.path.abspath('../'))

import dl_style_transfer.from_shake_yelp as yelp

from dl_style_transfer.workspace.kate_new import Kate
from sklearn.model_selection import train_test_split
from time import time

seed = 1337
np.random.seed(seed)

dataset = yelp.get_ryans_strange_input()
train, test = train_test_split(dataset)
kate = Kate(yelp.vocab_length(), 128, True, 32, 6.26)
kate.train(train, 100, 128)
kate.save_model(sys.argv[1])


def random_sample(data, num_samples):
    """Samples along first dimension of `data`"""
    idxs = np.random.choice(data.shape[0], size=num_samples, replace=False)
    return data[idxs]


def compute_accuracy(data, batch_size, start_stop_info=True, progress_interval=5):
    if start_stop_info:
        print("Computing accuracy for dataset of size", data.shape[0])

    n_batches = np.ceil(data.shape[0]/batch_size)

    accuracy = 0
    last_time = time()
    count = 0
    for i in range(0, data.shape[0], batch_size):
        batch = data[i:i+batch_size]
        reconstructed = kate.reconstruct(batch)
        accuracy += np.sum(reconstructed == batch)
        current_time = time()
        if progress_interval is not None and (current_time - last_time) >= progress_interval:
            last_time = current_time
            print("Computing accuracy. Percent complete:", 100*count/n_batches)
        count += 1

    if start_stop_info:
        print("Finished computing accuracy!")

    accuracy /= data.shape[0]
    return accuracy


batch_size = 128
num_samples = 50000
train_accuracy = compute_accuracy(random_sample(train, num_samples), batch_size)
test_accuracy = compute_accuracy(random_sample(test, num_samples), batch_size)
print("Training Accuracy:", train_accuracy)
print("Testing Accuracy:", test_accuracy)
