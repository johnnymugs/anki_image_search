#!/usr/bin/env python3
import ssl
from mimetypes import *
from urllib.request import *
from urllib.parse import *
from urllib.error import *

from . import shared
from .config import *

# unit -> unit
def read_netconfig():
  shared.config_netconfig = fill_config(
    shared.config_netconfigdefault,
    load_config(shared.s_NETWORK_CONFIG))

# unit -> unit
def write_netconfig():
  write_config(
    shared.config_netconfig,
    shared.s_NETWORK_CONFIG)

# unit -> unit
def install_proxy():
  config = shared.config_netconfig
  if config["use_system_proxy"]:
    d_s_proxy = {}
  else:
    s_proxy_addr = \
      config["proxy_addr"] + ":" + str(config["proxy_port"])
    d_s_proxy = \
      { "http" : s_proxy_addr
      , "https" : s_proxy_addr
      }
  install_opener(build_opener(ProxyHandler(d_s_proxy)))

  # haoxuany - appears to be a problem with Mac Python, and the
  # version of python runtime shipped with Anki
  # even worse is that during ssl verification host name matching is
  # dumb and broken: https://bugs.python.org/issue28414
  # as if working in China isn't bad enough, gross gross hack here:
  # https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error
  if config["assign_https_context"]:
    ssl._create_default_https_context = ssl._create_unverified_context

# string -> string
# haoxuany - Python doesn't handle any of this properly, nor does this. See:
# https://stackoverflow.com/questions/4389572/how-to-fetch-a-non-ascii-url-with-python-urlopen/29231552
def iri_to_uri(s_url):
  parse_result = urlparse(unquote(s_url))
  l_s_path = []
  for i, s_part in enumerate(parse_result):
    if i == 1:
      s_part = s_part.encode("idna").decode("utf-8")
    else:
      s_part = quote(s_part.encode("utf-8"), safe = "/;%[]=:$&()+,!?*@'~")
    l_s_path.append(s_part)
  return urlunparse(ParseResult(*l_s_path))

# string -> (byte * string option) + string as
# (byte * string option) option * (string option)
# because python is stupid and has no sums
def fetch_page(s_url):
  request = Request(iri_to_uri(s_url), headers = shared.d_s_SEND_HEADERS)

  install_proxy()
  # haoxuany - unfortunately we do this per request, since
  # there's too much state, and this could be modified by
  # someone else literally anywhere.

  try:
    with urlopen(request) as f_response:
      b_page = f_response.read()
      so_content_type = f_response.info().get_content_type()
      if so_content_type:
        so_ext = guess_extension(so_content_type)
      if not so_ext:
        so_ext = guess_type(s_url)
      return ((b_page, so_ext), None)
  except (URLError, HTTPError) as e:
    return (None, e.reason) # must this be a string? bleh
  # haoxuany - apparently other errors can occur, and
  # other exceptions thrown. Not my fault. Docs didn't say which.
