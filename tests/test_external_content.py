"""
Unit tests for external content such as recording, attachments which are stored
as URLs with a signature for the content stored else where.  Using
Leighton-Micali One Time Signature (RFC8554).
"""

import os
import pytest
import vcon
import vcon.security
import hsslms

call_data = {
      "epoch" : "1652552179",
      "destination" : "2117",
      "source" : "+19144345359",
      "rfc2822" : "Sat, 14 May 2022 18:16:19 -0000",
      "file_extension" : "WAV",
      "duration" : 94.84,
      "channels" : 1
}

@pytest.fixture(scope="function")
def empty_vcon() -> vcon.Vcon:
  """ construct vCon with no data """
  vCon = vcon.Vcon()
  return(vCon)

@pytest.fixture(scope="function")
def two_party_tel_vcon(empty_vcon : vcon.Vcon) -> vcon.Vcon:
  """ construct vCon with two tel URL """
  vCon = empty_vcon
  first_party = vCon.set_party_tel_url(call_data['source'])
  second_party = vCon.set_party_tel_url(call_data['destination'])
  return(vCon)

def test_lm_ots_sign() -> None:
  file_size = 2048
  fake_file = os.urandom(file_size)

  key, sig = vcon.security.lm_one_time_signature(fake_file)

  vcon.security.verify_lm_one_time_signature(fake_file, sig, key)

  try:
    # cause signature to fail
    vcon.security.verify_lm_one_time_signature(fake_file, sig.replace("D", "E", 1), key)
    raise Exception("Should have raisee and INVALID signature error")

  except hsslms.utils.INVALID as invalid_error:
    # Expect this to be raised as we have modified signature
    pass

  try:
    # cause key to fail
    vcon.security.verify_lm_one_time_signature(fake_file, sig, key.replace("A", "Z", 1))
    raise Exception("Should have raised and INVALID key error")

  except hsslms.utils.INVALID as invalid_error:
    # Expect this to be raised as we have modified signature
    pass

def test_external_recording(two_party_tel_vcon : vcon.Vcon) -> None:
  data_size = 4096
  data = os.urandom(data_size)

  url = "https://example.com?q=\"ddd\"&y=\'!\'"
  #print("url: {}".format(url))

  file_name = "my_rec.wav"

  assert(vcon.Vcon.MIMETYPE_WAV == "audio/x-wav")

  two_party_tel_vcon.add_dialog_external_recording(data,
    call_data["rfc2822"],
    call_data["duration"],
    0,
    url,
    vcon.Vcon.MIMETYPE_WAV,
    file_name)

  vcon_json = two_party_tel_vcon.dumps()

  new_vcon = vcon.Vcon()
  new_vcon.loads(vcon_json)

  assert(len(new_vcon.dialog) == 1)
  assert(new_vcon.dialog[0]['type'] == "recording")
  assert(new_vcon.dialog[0]['url'] == url)
  assert(new_vcon.dialog[0]['parties'] == 0)
  assert(new_vcon.dialog[0]['start'] == call_data["rfc2822"])
  assert(new_vcon.dialog[0]['duration'] == call_data["duration"])
  assert(new_vcon.dialog[0]['mimetype'] == "audio/x-wav")
  assert(new_vcon.dialog[0]['filename'] == file_name)
  assert("body" not in new_vcon.dialog[0])

  new_vcon.verify_dialog_external_recording(0, data)

  try:
    # Change the data so that validation should fail
    new_vcon.verify_dialog_external_recording(0, data[1:])
    raise Exception("Should have raised exception here as data is missin the first byte")

  except hsslms.utils.INVALID as invalid_error:
    # Expect to get this exception
    pass

