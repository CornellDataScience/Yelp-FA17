import tensorflow as tf
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('../'))
from dl_style_transfer.layers.layers import xavier_initializer


class TextCNN(object):
    """
    A CNN for text classification.
    Uses an embedding layer, followed by a convolutional, max-pooling and softmax layer.
    """
    def __init__(
      self, num_reconstructions, trained_model):
        self.num_reconstructions = num_reconstructions
        self.sequence_length = trained_model.sequence_length
        self.num_classes = trained_model.num_classes
        self.vocab_size = trained_model.vocab_size
        self.embedding_size = trained_model.embedding_size
        self.filter_sizes = trained_model.filter_sizes
        self.num_filters = trained_model.num_filters
        self.l2_reg_lambda = trained_model.l2_reg_lambda

        # Placeholders for input, output and dropout
        self.input_x = tf.get_variable("input_x", shape=[self.num_reconstructions, self.sequence_length], trainable=False)
        self.dropout_keep_prob = tf.placeholder(tf.float32, name="dropout_keep_prob")

        # Keeping track of l2 regularization loss (optional)
        l2_loss = tf.constant(0.0)

        # Embedding layer
        with tf.variable_scope("embedding", reuse=True):
            self.W = tf.get_variable(
                name="W", trainable=False)
            self.embedded_chars = tf.nn.embedding_lookup(self.W, self.input_x)
            self.embedded_chars_expanded = tf.expand_dims(self.embedded_chars, -1)

        # Create a convolution + maxpool layer for each filter size
        pooled_outputs = []
        for i, filter_size in enumerate(self.filter_sizes):
            with tf.variable_scope("conv-maxpool-%s" % filter_size, reuse=True):
                # Convolution Layer
                filter_shape = [filter_size, self.embedding_size, 1, self.num_filters]
                W = tf.get_variable(name="W", trainable=False)
                b = tf.get_variable(name="b", trainable=False)
                conv = tf.nn.conv2d(
                    self.embedded_chars_expanded,
                    W,
                    strides=[1, 1, 1, 1],
                    padding="VALID",
                    name="conv")
                # Apply nonlinearity
                h = tf.nn.relu(tf.nn.bias_add(conv, b), name="relu")
                # Maxpooling over the outputs
                pooled = tf.nn.max_pool(
                    h,
                    ksize=[1, self.sequence_length - filter_size + 1, 1, 1],
                    strides=[1, 1, 1, 1],
                    padding='VALID',
                    name="pool")
                pooled_outputs.append(pooled)

        # Combine all the pooled features
        num_filters_total = self.num_filters * len(self.filter_sizes)
        self.h_pool = tf.concat(pooled_outputs, 3)
        self.h_pool_flat = tf.reshape(self.h_pool, [-1, num_filters_total])

        # Add dropout
        with tf.variable_scope("dropout"):
            self.h_drop = tf.nn.dropout(self.h_pool_flat, self.dropout_keep_prob)

        # Final (unnormalized) scores and predictions
        with tf.variable_scope("output", reuse=True):
            W = tf.get_variable(
                "W", trainable=False)
            b = tf.get_variable(name="b", trainable=False)
            l2_loss += tf.nn.l2_loss(W)
            l2_loss += tf.nn.l2_loss(b)
            self.scores = tf.nn.xw_plus_b(self.h_drop, W, b, name="scores")
            self.predictions = tf.argmax(self.scores, 1, name="predictions")
