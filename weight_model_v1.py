"""
@Project   : tf-gpu
@Module    : weight_model_v1.py
@Author    : Jeff [arfu.guo@gmail.com]
@Created   : 2018/12/28 下午9:23
@Desc      : 
"""
import tensorflow as tf


def neural_net_text_input(text_vector_len, name):
    """
    Return a Tensor for a batch of text input
    : text_vector_len: Length of text vector
    : return: Tensor for text vector input.
    """
    return tf.placeholder(tf.float32, [None, text_vector_len], name=name)


def neural_net_label_input(n_classes):
    """
    Return a Tensor for a batch of label input
    : n_classes: Number of classes
    : return: Tensor for label input.
    """
    return tf.placeholder(tf.float32, [None, n_classes], 'y')


def neural_net_weight_tensor(word_weights):
    """
    Return a Tensor for the weight matrix
    :param word_weights: List<Double>
    :return: A matrix tensor
    """
    d = len(word_weights)
    matrix = []

    for idx, weight in enumerate(word_weights):
        diag = tf.Variable([weight], trainable=True)
        diag_before = [0.0]*idx
        diag_before = tf.constant(diag_before)
        diag_after = [0.0]*(d-1-idx)
        diag_after = tf.constant(diag_after)
        row = tf.concat(values=[diag_before, diag, diag_after], axis=0)
        matrix.append(row)

    matrix = [[row] for row in matrix]
    matrix = tf.concat(values=matrix, axis=0)

    return matrix


def neural_net_weight_tensor_test():

    matrix = neural_net_weight_tensor([100.0, 10.0, 1.0])

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        print(sess.run(matrix))


def vector_transform(init_weight, input_tensor):
    """
    Convert a matrix of sentence vectors to another matrix
    init_weight: list
    input_tensor: tensor
    :return: a matrix tensor
    """
    weight_matrix = neural_net_weight_tensor(init_weight)
    output = tf.matmul(input_tensor, weight_matrix)

    return output


def similarity_matrix(init_weight, input_host, input_guest):
    """
    给一组句子host，给一组句子guest，算guest和host的相似度
    init_weight: list
    input_host: tensor
    input_guest: tensor
    :return: a tensorflow matrix tensor
    """
    # output_host = vector_transform(init_weight, input_host)
    # output_guest = vector_transform(init_weight, input_guest)
    weight_matrix = neural_net_weight_tensor(init_weight)
    output_host = tf.matmul(input_host, weight_matrix)
    output_guest = tf.matmul(input_guest, weight_matrix)
    similarity = tf.matmul(output_guest, tf.transpose(output_host))

    return similarity


def similarity_test():

    host = [[1, 0, 1, 0], [1, 1, 1, 1]]
    guest = [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 1, 1], [0, 0, 0, 0]]
    init_weight = [1.0, 2.0, 1.0, 1.0]

    input_host = neural_net_text_input(len(init_weight), "input_host")
    input_guest = neural_net_text_input(len(init_weight), "input_guest")
    similarity = similarity_matrix(init_weight, input_host, input_guest)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        print(sess.run(similarity, feed_dict={
            input_host: host,
            input_guest: guest
        }))


def get_probabilities_cost(init_weight, input_host, input_guest, y):
    """
    计算每个样本在各个类别的概率

    init_weight: list
    input_host: tensor
    input_guest: tensor
    y: tensor
    :return: optimizer
    """

    similarity = similarity_matrix(init_weight, input_host, input_guest)

    logits = tf.identity(similarity, name='logits')

    cost = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits, labels=y))
    return cost


def probability_test():
    host = [[1, 0, 1, 0], [1, 1, 1, 1]]
    guest = [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 1, 1], [0, 0, 0, 0]]
    labels = [[1, 0], [1, 0], [0, 1], [0, 1]]
    init_weight = [1.0, 2.0, 1.0, 1.0]

    input_host = neural_net_text_input(len(init_weight), "input_host")
    input_guest = neural_net_text_input(len(init_weight), "input_guest")
    y = neural_net_label_input(2)

    cost = get_probabilities_cost(init_weight, input_host, input_guest, y)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        print(sess.run(cost, feed_dict={
            input_host: host,
            input_guest: guest,
            y: labels
        }))


def get_optimizer_single(init_weight, input_host, input_guest, y):
    """
    host中每个类别只有一个句子; 完成一次梯度下降
    :return: optimizer
    """

    cost = get_probabilities_cost(init_weight, input_host, input_guest, y)
    optimizer = tf.train.AdamOptimizer().minimize(cost)

    return optimizer


def get_accuracy(similarity, y):
    """
    计算正确率
    :param similarity: tensor
    :param y: placeholder
    :return: tensor
    """
    correct_pred = tf.equal(tf.argmax(similarity, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32),
                              name='accuracy')
    return accuracy


def run_optimizer():

    host = [[1, 0, 1, 0], [1, 1, 1, 1]]
    guest = [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 1, 1], [0, 0, 0, 0]]
    labels = [[1, 0], [1, 0], [0, 1], [0, 1]]
    init_weight = [1.0, 2.0, 1.0, 1.0]

    input_host = neural_net_text_input(len(init_weight), "input_host")
    input_guest = neural_net_text_input(len(init_weight), "input_guest")
    y = neural_net_label_input(2)

    similarity = similarity_matrix(init_weight, input_host, input_guest)

    optimizer = get_optimizer_single(init_weight, input_host, input_guest, y)

    cost = get_probabilities_cost(init_weight, input_host, input_guest, y)

    accuracy = get_accuracy(similarity, y)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        sess.run(optimizer, feed_dict={
            input_host: host,
            input_guest: guest,
            y: labels
        })

        loss = sess.run(cost, feed_dict={
            input_host: host,
            input_guest: guest,
            y: labels
        })
        valid_acc = sess.run(accuracy, feed_dict={
            input_host: host,
            input_guest: guest,
            y: labels
        })

        print('Loss: {:>10.4f} Training Accuracy: {:.6f}'.format(
            loss, valid_acc))


if __name__ == '__main__':

    # neural_net_weight_tensor_test()

    # similarity_test()

    # probability_test()

    run_optimizer()
