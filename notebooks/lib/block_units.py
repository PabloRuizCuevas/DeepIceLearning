from keras.models import Model
import keras.layers
from keras.layers.core import Activation, Layer
import keras.backend as K

def conv3d_bn(x, filters, filter_size, padding='same',
              strides=(1, 1, 1), name=None):
    """Utility function to apply conv + BN.
    # Arguments
        x: input tensor.
        filters: filters in `Conv2D`.
        num_row: height of the convolution kernel.
        num_col: width of the convolution kernel.
        padding: padding mode in `Conv2D`.
        strides: strides in `Conv2D`.
        name: name of the ops; will become `name + '_conv'`
            for the convolution and `name + '_bn'` for the
            batch norm layer.
    # Returns
        Output tensor after applying `Conv2D` and `BatchNormalization`.
    """
    if name is not None:
        bn_name = name + '_bn'
        conv_name = name + '_conv'
    else:
        bn_name = None
        conv_name = None
    channel_axis = 1 if K.image_data_format() == 'channels_first' else -1
    x = keras.layers.Conv3D(
        filters, filter_size,
        strides=strides,
        padding=padding,
        use_bias=False,
        name=conv_name)(x)
    x = keras.layers.BatchNormalization(axis=channel_axis, scale=False, name=bn_name)(x)
    x = keras.layers.Activation('relu', name=name)(x)
    return x
