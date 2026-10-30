from tensorflow import keras
from tensorflow.keras import layers

from config import IMG_SIZE

# Both models share the same layout so Grad-CAM works on either:
# [augmentation] -> [rescale] -> backbone -> GAP -> Dropout -> Dense(sigmoid)


def _augment():
    return keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.1),
        ],
        name="augmentation",
    )


def _head(x):
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    return layers.Dense(1, activation="sigmoid")(x)


def build_mobilenet():
    inputs = keras.Input((IMG_SIZE, IMG_SIZE, 3))
    x = _augment()(inputs)
    x = layers.Rescaling(1 / 127.5, offset=-1)(x)
    base = keras.applications.MobileNetV2(
        include_top=False, weights="imagenet", input_shape=(IMG_SIZE, IMG_SIZE, 3), name="backbone"
    )
    base.trainable = False
    x = base(x, training=False)
    return keras.Model(inputs, _head(x), name="kidney_mobilenetv2"), base


def build_cnn():
    inputs = keras.Input((IMG_SIZE, IMG_SIZE, 3))
    x = _augment()(inputs)
    x = layers.Rescaling(1 / 127.5, offset=-1)(x)
    backbone = keras.Sequential(name="backbone")
    backbone.add(keras.Input((IMG_SIZE, IMG_SIZE, 3)))
    for f in (32, 64, 128, 128):
        backbone.add(layers.Conv2D(f, 3, padding="same", use_bias=False))
        backbone.add(layers.BatchNormalization())
        backbone.add(layers.ReLU())
        backbone.add(layers.MaxPooling2D())
    x = backbone(x)
    return keras.Model(inputs, _head(x), name="kidney_cnn"), backbone


def compile_model(model, lr):
    model.compile(
        optimizer=keras.optimizers.Adam(lr),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.AUC(name="auc"),
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )