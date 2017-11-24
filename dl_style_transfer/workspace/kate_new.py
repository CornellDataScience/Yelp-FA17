from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import tensorflow as tf
import numpy as np
import os
import math

from dl_style_transfer.layers.layers import *
from time import time, strftime


class Kate:

    def __init__(self, embedding_size, vocab_size, max_seq_len, k, alpha, learning_rate=0.001, load_model=None):
        self._vocab_size = vocab_size
        self._k = k
        self._alpha = alpha

        print("Constructing KATE architecture...")
        self._graph = tf.Graph()
        with self._graph.as_default():
            self._x = tf.placeholder(tf.int32, shape=[None, max_seq_len], name='X')
            self._phase_train = tf.placeholder(tf.bool, name='Phase')

            hot = tf.one_hot(self._x, depth=vocab_size, name='Hot')

            with tf.variable_scope('Encoder'):
                fc1, var_dict = fc(hot, embedding_size, activation=tf.nn.tanh, scope='FC1')

                k1 = k_comp(fc1, self._phase_train, k, alpha=alpha, scope='K-Comp1')

            with tf.variable_scope('Decoder'):
                weights = var_dict['Weights']  # Use same weights from encoder
                bias = tf.get_variable('Scores', initializer=xavier_initializer((vocab_size,)))
                scores = k1 * weights + bias  # Effectively transpose multiply
                self._y_hat = tf.nn.softmax(scores, name='Y-Hat')
                self._pred = tf.argmax(self._y_hat, axis=-1, name='Predicted')

            with tf.variable_scope('Loss'):
                self._loss = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=scores, labels=self._x, name='Loss')
                self._train_step = tf.train.AdamOptimizer(learning_rate).minimize(self._loss)

            self._sess = tf.Session()
            with self._sess.as_default():
                self._saver = tf.train.Saver()
                if load_model is not None:
                    print("Restoring Model...")
                    load_model = os.path.abspath(load_model)
                    self._saver.restore(self._sess, load_model)
                    print("Model Restored!")
                else:
                    print("Initializing model...")
                    self._sess.run(tf.global_variables_initializer())
                    print("Model Initialized!")

    def train(self, x_train, n_epochs, batch_size, start_stop_info=True, progress_interval=5):
        training_size = x_train.shape[0]

        # Training loop for parameter tuning
        if start_stop_info:
            print("Starting training for %d epochs" % n_epochs)

        batch_per_epoch = math.ceil(training_size/batch_size)
        n_batch = n_epochs*batch_per_epoch
        last_time = time()
        for epoch in range(n_epochs):
            perm = np.random.permutation(training_size)
            for i in range(0, training_size, batch_size):
                idx = perm[i:i + batch_size]
                x_batch = x_train[idx]
                _, loss_val = self._sess.run(self._train_step, feed_dict={self._x: x_batch})
                current_time = time()
                if progress_interval is not None and (current_time - last_time) >= progress_interval:
                    last_time = current_time
                    print("Current Loss Value: %.10f, Percent Complete: %.4f" %
                          (loss_val, (epoch*batch_per_epoch + i) / n_batch * 100))
        if start_stop_info:
            print("Completed Training.")
        return loss_val

    def apply(self, x_data):
        """Applies the model to the batch of data provided. Typically called after the model is trained.

        Args:
            x_data:  A numpy ndarray of the data to apply the model to. Should have the same shape as the training data,
                e.g. `[batch_size, sentence_length]`.

        Returns:
            A numpy ndarray of the data, with shape `[batch_size, sentence_length, embedding_size]`
        """
        with self._sess.as_default():
            return self._sess.run(self._y_hat, feed_dict={self._x: x_data, self._phase_train: False})

    def save_model(self, save_path=None):
        """Saves the model in the specified file.
        Args:
            save_path:  The relative path to the file. By default, it is
                saved/KATE-Year-Month-Date_Hour-Minute-Second.ckpt
        """
        with self._sess.as_default():
            print("Saving Model")
            if save_path is None:
                save_path = "saved/KATE-%s.ckpt" % strftime("%Y-%m-%d_%H-%M-%S")
            dirname = os.path.dirname(save_path)
            if dirname is not '':
                os.makedirs(dirname, exist_ok=True)
            save_path = os.path.abspath(save_path)
            path = self._saver.save(self._sess, save_path)
            print("Model successfully saved in file: %s" % path)


def main():
    pass


if __name__ == "__main__":
    main()