# Futhark with Fangs!

Futhark with Fangs is a small Python script that provides a web API to
a [Futhark](https://futhark-lang.org) program.  You thought GPU
performance was inhibited by PCI Express bandwidth?  Just wait until
you have tried tunneling all your data over HTTP!

## Usage

Create an amazing Futhark program, say, `futapp.fut`:

```
entry dotprod (xs: []i32) (ys: []i32) = reduce (+) 0 (map2 (+) xs ys)

entry sumrows (xss: [][]i32) = map (reduce (+) 0) xss
```

Compile it to a Python module:

```
$ futhark pyopencl --library futapp.fut
```

Give it some fangs!

```
$ ./futhark_with_fangs.py futapp
```

Now go to another shell and POST some data with
[curl](https://curl.haxx.se/), or your favourite HTTP library in your
favourite programming language:

```
$ echo '[1,2] [3,4]' | curl -X POST --data-binary @- localhost:8000/dotprod
10i32
```

If an error occurs, you will probably get an appropriate HTTP status
code back (404 for missing entry point, 400 if you pass it bad data,
500 if it fails for some other reason).

## Options

By default, `futhark_with_fangs.py` listens on port 8000 on localhost.
Use `--port` and ``--host`` to change it.

## Requirements

* Python 3 (this is 2018, people)
* PyOpenCL
* Numpy
* Futhark 0.4.1 or newer.

If you are lucky, you can run `pip3 install -r requirements.txt` to
get the Python dependencies.
