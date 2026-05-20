"""ML support package: shared schema, feature builder, labels, and model registry.

Used both by Django (serving) and mlops/ pipelines (training) to guarantee
training-serving consistency. NO training code lives here.
"""
