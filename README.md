# recipe-app-beeware

- https://docs.beeware.org/en/latest/tutorial/tutorial-1.html

# Install

```
conda create -n beeware-env python=3.8 ipython jupyter

pip install briefcase
```

# Bootstrap

```
briefcase new

cd ./app-name
briefcase dev

# In case of error

export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libffi.so.7
```

# Packaging

```
# Create packaing scaffold
briefcase create

# Build application
briefcase build

# Test run
briefcase run

# Package application
briefcase package
```

# Android Build

```
briefcase update android
briefcase build android
briefcase run android
```

