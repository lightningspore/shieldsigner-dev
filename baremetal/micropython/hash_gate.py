# SPDX-License-Identifier: MIT
# Generated public data only; CPython reference plus RFC4231/RFC6070/BIP39 cases.
import hashlib
import hmac
import binascii
import gc
import time
import camera
baseline=camera.settings()['rust_heap_bytes']
name='sha224'
assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==(28,64)
data=bytes((i*17+11)&255 for i in range(0))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='0dda739c0d523bd5d145158ffa5b27f86b62a0c0452458e9c8d08bcb'
assert copy.hexdigest()=='d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f'
del state,copy
data=bytes((i*17+11)&255 for i in range(1))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='6dfd77d537723be7fdf7e16b606c2eff4263a0685d3449e4404ebeb8'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='0280198cc2e0f6ba25ccbd4b0f60c2383fd1d28665f525812e5d7d99'
assert copy.hexdigest()=='6dfd77d537723be7fdf7e16b606c2eff4263a0685d3449e4404ebeb8'
del state,copy
data=bytes((i*17+11)&255 for i in range(55))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a0f31e03660160b997ed538bc9b870495f84a45e69b91cde5a948f00'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='37ed43d5cc751125c67747c2a5d1f033fcc65bf0c093e2de04695525'
assert copy.hexdigest()=='a0f31e03660160b997ed538bc9b870495f84a45e69b91cde5a948f00'
del state,copy
data=bytes((i*17+11)&255 for i in range(56))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='407f47e1bef123157e5456a22a762e15d910ac40123e611fa7367d41'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='dfba34d6cefb7c1d3b4a8ea1a57f0da785314c7e03c2e9bd6f7fcd9e'
assert copy.hexdigest()=='407f47e1bef123157e5456a22a762e15d910ac40123e611fa7367d41'
del state,copy
data=bytes((i*17+11)&255 for i in range(63))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='eec480e0af810afd1bcd1567e295f4673e040c0caac8858c82e05ffd'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='818f1c7448c0f202120abed2720ffa85d76fc2e908e24e95820d7d0c'
assert copy.hexdigest()=='eec480e0af810afd1bcd1567e295f4673e040c0caac8858c82e05ffd'
del state,copy
data=bytes((i*17+11)&255 for i in range(64))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='4e1c7f989b1994ff09c813d10ca86deb702164a837887e5c30b19d06'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='0c46339c0808cec3f9f051b222fdcdbb271833e5c2ccf3e35dbc162d'
assert copy.hexdigest()=='4e1c7f989b1994ff09c813d10ca86deb702164a837887e5c30b19d06'
del state,copy
data=bytes((i*17+11)&255 for i in range(65))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='99690c951bba83fa89ab58e3d879f5cda8a4a8c037f0c644748314b7'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='ec735b81352f0155cf485363fd8c830baa379c2efd18a522ee6789b7'
assert copy.hexdigest()=='99690c951bba83fa89ab58e3d879f5cda8a4a8c037f0c644748314b7'
del state,copy
data=bytes((i*17+11)&255 for i in range(111))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='4a0312415e4f6dce2d58c81a44c71fc2544ebd002f084cea0e85a7e5'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='9a2b8254a8c1533991d32e867769624a6a45cd34a868284ab340c28d'
assert copy.hexdigest()=='4a0312415e4f6dce2d58c81a44c71fc2544ebd002f084cea0e85a7e5'
del state,copy
data=bytes((i*17+11)&255 for i in range(112))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='042e8917f66d0932bbf4bb199966dfe60e2d4bf9e04be1741912e73a'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='186712d24272057f23c61d2fc3de40fd2c30d49b05041b8856d4ebf0'
assert copy.hexdigest()=='042e8917f66d0932bbf4bb199966dfe60e2d4bf9e04be1741912e73a'
del state,copy
data=bytes((i*17+11)&255 for i in range(127))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='c19b97bbf691b3ab84b685b148e81b4e6cf8fc070613b00d29f6a1b3'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='16499a4c4a50a3d83ddd0fdcad13b8aaef37a1bbf50bf74fce14eeb6'
assert copy.hexdigest()=='c19b97bbf691b3ab84b685b148e81b4e6cf8fc070613b00d29f6a1b3'
del state,copy
data=bytes((i*17+11)&255 for i in range(128))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a18baa8129e1a1e80a3d9c17a3d51eb5240b8386a8bfdcb136c72a3b'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='b0002f3773a112d09958039aec9d89a17c006123cc87feecdc083de4'
assert copy.hexdigest()=='a18baa8129e1a1e80a3d9c17a3d51eb5240b8386a8bfdcb136c72a3b'
del state,copy
data=bytes((i*17+11)&255 for i in range(129))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='1d11fef999b3cef7e80a2a5251424b6cc3b456c7ab54290429463b10'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='d7a31fafb168eded77b3745c845967e70c1aa5313f2165f0da243ae1'
assert copy.hexdigest()=='1d11fef999b3cef7e80a2a5251424b6cc3b456c7ab54290429463b10'
del state,copy
data=bytes((i*17+11)&255 for i in range(1024))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='974563dbd4a832e803be5aa175b53f781fa2532dbfaa18c32dae7fbc'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='b52f03da97ea08580c1841e497584f9cc995a4dbd345ade16e848a35'
assert copy.hexdigest()=='974563dbd4a832e803be5aa175b53f781fa2532dbfaa18c32dae7fbc'
del state,copy
key=b'public key'
msg=b'public message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='fe9741458a32b807c5576977341bebd953e969f9ae3b4e5e77d8f2c7'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='fe9741458a32b807c5576977341bebd953e969f9ae3b4e5e77d8f2c7'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'
msg=b'Hi There'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='896fb1128abbdf196832107cd49df33f47b4b1169912ba4f53684b22'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='896fb1128abbdf196832107cd49df33f47b4b1169912ba4f53684b22'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
msg=b'public long-key message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='4723d3db0028e875affa33c71ac56265bafd405330517bf62a3153c0'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='4723d3db0028e875affa33c71ac56265bafd405330517bf62a3153c0'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b''
msg=b''
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='5ce14f72894662213e2748d2a6ba234b74263910cedde2f5a9271524'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='5ce14f72894662213e2748d2a6ba234b74263910cedde2f5a9271524'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',1,1)).decode()=='d6'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',2,28)).decode()=='550d347d235a844c8ef1cd5710a065467c557e89f18c508f5b59b7cf'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',65,29)).decode()=='bd301141f3e241fbf29f87654cccbafc8252172c5e9ea42c9af3a4deb8'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',127,57)).decode()=='65d1141d1031b446e7a4564bbfc246fd414cd186343b1af4dc087c1624b9c45779298e44219b58e58e6332ee7338f468d06417a94f16327715'
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@HASH_ALGORITHM_PASS',name)
name='sha256'
assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==(32,64)
data=bytes((i*17+11)&255 for i in range(0))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='2bf39a66d02da3b6b06655fa5c61d4c267509c5fa59634c26bc80d3ae46a6c4f'
assert copy.hexdigest()=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
del state,copy
data=bytes((i*17+11)&255 for i in range(1))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e7cf46a078fed4fafd0b5e3aff144802b853f8ae459a4f0c14add3314b7cc3a6'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='be212bc42fc80644512d523a1a3c675fb8bdb40393f2868cbf80724a93df0762'
assert copy.hexdigest()=='e7cf46a078fed4fafd0b5e3aff144802b853f8ae459a4f0c14add3314b7cc3a6'
del state,copy
data=bytes((i*17+11)&255 for i in range(55))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='96ad1190c508d579299430c401f0feadb3d91db82a47e970ca3c0e81b9077052'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='da1e9fe1e1817553ba269d47cfcdca25a5fde350e25de50b86977c45ce948ebb'
assert copy.hexdigest()=='96ad1190c508d579299430c401f0feadb3d91db82a47e970ca3c0e81b9077052'
del state,copy
data=bytes((i*17+11)&255 for i in range(56))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='9c6bf72d0d816db9ce0a842b591e8d22bbe7ef00d8da6e05833bf76c86ffc083'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='b24aef72051608346707908ce822de044bb12fc8e834437d120b0c0f4ffff801'
assert copy.hexdigest()=='9c6bf72d0d816db9ce0a842b591e8d22bbe7ef00d8da6e05833bf76c86ffc083'
del state,copy
data=bytes((i*17+11)&255 for i in range(63))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='b27229bce9210125046870f2cea08c02499c0c932abb717af9605541caa6cd41'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='c35b8f8c49972826a18dfc36deccc03541b68b5b12fedbe8d49aee3c6e9e5817'
assert copy.hexdigest()=='b27229bce9210125046870f2cea08c02499c0c932abb717af9605541caa6cd41'
del state,copy
data=bytes((i*17+11)&255 for i in range(64))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='c48fb39d22a7c0e03edd658015d234744d734a3b22ca895c15bdcf7953401812'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='26725167f3a36f90a4d4249034ace12c888c407a141f243e6f5ccf0ca167e511'
assert copy.hexdigest()=='c48fb39d22a7c0e03edd658015d234744d734a3b22ca895c15bdcf7953401812'
del state,copy
data=bytes((i*17+11)&255 for i in range(65))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='374f90bd4718795dfb7d0201b6056b57effbb0a37eee880e62f1e8df38547be7'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='e2f3d248377845da568301912f335c6f4e3086efe5f40b34ed515923cb394611'
assert copy.hexdigest()=='374f90bd4718795dfb7d0201b6056b57effbb0a37eee880e62f1e8df38547be7'
del state,copy
data=bytes((i*17+11)&255 for i in range(111))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e399a3e5e0f609fec5de8691df594fedb03c7bcb1bc414edabc85b189865a4e7'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='7dee3e4fcfa6eeebd7a1f8ebd02ddbf468bb3bbbeaa0d2005e3fd384a0c9766d'
assert copy.hexdigest()=='e399a3e5e0f609fec5de8691df594fedb03c7bcb1bc414edabc85b189865a4e7'
del state,copy
data=bytes((i*17+11)&255 for i in range(112))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='39ef6c83d2c50b2e8a53b5d76f26515909581c45f8a0094504f19372d1d1f087'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='956c61e8f2ced4cd5f1c12bbce2ce37ae07e5f4f1fcbaae29a58579a2e1aa5c9'
assert copy.hexdigest()=='39ef6c83d2c50b2e8a53b5d76f26515909581c45f8a0094504f19372d1d1f087'
del state,copy
data=bytes((i*17+11)&255 for i in range(127))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e84ee42f69598e5950aa99eeefa9735e0a580ac7b2f5439adafda30586ac4027'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='c5139f5e8a2abd41c3c4a3da15657239fef9babfaed1b765b863e1d076198c27'
assert copy.hexdigest()=='e84ee42f69598e5950aa99eeefa9735e0a580ac7b2f5439adafda30586ac4027'
del state,copy
data=bytes((i*17+11)&255 for i in range(128))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a024b23bfe4e9ae032cd2eca374b33360f0e4ff13830e377f7970119b64f087d'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='ab99045bfa8c2666692ff1927e669bf2c7488f6550dee894ac35863a173f927c'
assert copy.hexdigest()=='a024b23bfe4e9ae032cd2eca374b33360f0e4ff13830e377f7970119b64f087d'
del state,copy
data=bytes((i*17+11)&255 for i in range(129))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='350f1bef21c3bb90edff9404068816b7e5d60c35034f96a55b481e4d0f90a874'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='3a79219b1a13d3d6e5d685d604c2062f3abcf1867623985201020e48d03da790'
assert copy.hexdigest()=='350f1bef21c3bb90edff9404068816b7e5d60c35034f96a55b481e4d0f90a874'
del state,copy
data=bytes((i*17+11)&255 for i in range(1024))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='db548a477d35e6b7ac3b4421c81517e505b966b6389cd42baf4154124befed3a'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='f85d586d8b45b9f07b169e6a4768a50919d8ed8d8e79689c63cc57b57b278e0b'
assert copy.hexdigest()=='db548a477d35e6b7ac3b4421c81517e505b966b6389cd42baf4154124befed3a'
del state,copy
key=b'public key'
msg=b'public message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='e06d6cdd194ce277a4afa33f9c3cdf12640898ef4f01e0f3fc9112084725daa1'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='e06d6cdd194ce277a4afa33f9c3cdf12640898ef4f01e0f3fc9112084725daa1'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'
msg=b'Hi There'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
msg=b'public long-key message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='5d73206cf65896a53c3911f3c75155d7fa7bc0fb6e0081c18c0af3840a340e1e'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='5d73206cf65896a53c3911f3c75155d7fa7bc0fb6e0081c18c0af3840a340e1e'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b''
msg=b''
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='b613679a0814d9ec772f95d778c35fc5ff1697c493715653c6c712144292c5ad'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='b613679a0814d9ec772f95d778c35fc5ff1697c493715653c6c712144292c5ad'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',1,1)).decode()=='6a'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',2,32)).decode()=='4d5b5c18e8f8ccd8a0dad0bc3d5fec13b0c591e96240d8493c1603be0905256e'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',65,33)).decode()=='b563750059468d232822572a045b9a6a6a1bf0f094bef23ad99e20e50058413058'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',127,65)).decode()=='78916678f572c0529014e13d3bab7247012f05f2933d3d475d8d52bda2e66665574356456e912ba69dab93cf180d21943dde6ef90949d0d0fdf83c55f1cec44b43'
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@HASH_ALGORITHM_PASS',name)
name='sha384'
assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==(48,128)
data=bytes((i*17+11)&255 for i in range(0))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='71bff9cefecaf40ab670f37d7ff550da3c29920740e6df10f7bed9665657752190c49bad88d34505e722e0a62b700c6c'
assert copy.hexdigest()=='38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b'
del state,copy
data=bytes((i*17+11)&255 for i in range(1))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='2deb5d512a82fb61b846799f41367b0172a8a82a4b1539fa9f3fd148bdd1db7eb053b452eb916523186cbbe41e9f2fbb'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='7524d124c526e58c03234056ac706442bce62442573e5325d86a644caf5bd31b12db479538c724f1d0bf6f3cd3700f9e'
assert copy.hexdigest()=='2deb5d512a82fb61b846799f41367b0172a8a82a4b1539fa9f3fd148bdd1db7eb053b452eb916523186cbbe41e9f2fbb'
del state,copy
data=bytes((i*17+11)&255 for i in range(55))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='cf035be8aee7dcc1633a5e9b042880d603ebd9086781e423239023141e450e6764d01783dfec21dcf94152196d887f65'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='07938ce2d9b0b418c72412988d4205fbe350886330aab7349d6408bc356f884bec959c0d9007886e60d915fed1a800f0'
assert copy.hexdigest()=='cf035be8aee7dcc1633a5e9b042880d603ebd9086781e423239023141e450e6764d01783dfec21dcf94152196d887f65'
del state,copy
data=bytes((i*17+11)&255 for i in range(56))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e15d5cdfd2785da070041dfaab9526d50391ee594c26c83067f2290919eb03b7b393c07e236eea52332c95f6c26a8fa8'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='157c01dcc1af22c579ccbc4726a1da1c27f4ba463152cad6d76d89fb07c8a4378903965d467e43b9a9413328ee8848cf'
assert copy.hexdigest()=='e15d5cdfd2785da070041dfaab9526d50391ee594c26c83067f2290919eb03b7b393c07e236eea52332c95f6c26a8fa8'
del state,copy
data=bytes((i*17+11)&255 for i in range(63))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='50a232ea6c23aeb02a852ba956d447c328bff11ba3dfc2ff7d63433a0b934baa4a035f7947b8a9964d8246ef1491cac2'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='05ac28bb4200a20e4fd1011fb8ea3d065965809618d2998856d531b0fa3f7791b572d2e84b21323bc428fe0d9f1fb118'
assert copy.hexdigest()=='50a232ea6c23aeb02a852ba956d447c328bff11ba3dfc2ff7d63433a0b934baa4a035f7947b8a9964d8246ef1491cac2'
del state,copy
data=bytes((i*17+11)&255 for i in range(64))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='f627cf8650797d7e95a6fd39eae4cc8e5ee54b776ca79fbc4f7d00fc9f9b9e85c72b20f7f05a5abcf9a1d71b03e778b5'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='faa7d37e89fef28dd1519c070f63e349e08f1a52b04d57dfe783628e573814efff6381c503a2a2eebb39e863094d1065'
assert copy.hexdigest()=='f627cf8650797d7e95a6fd39eae4cc8e5ee54b776ca79fbc4f7d00fc9f9b9e85c72b20f7f05a5abcf9a1d71b03e778b5'
del state,copy
data=bytes((i*17+11)&255 for i in range(65))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='092b4ff37f20427fc12d59decbcb236b9d1b954ffc8b50339233874cdcf98cae2b1c6502c64056cb621d9c94797aefd2'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='2e2f2a81415c4a96cd79d233f05204c831f24e97509b1d67d0ce46051a5e00070e21539b227583e51580fdb5f4fda04d'
assert copy.hexdigest()=='092b4ff37f20427fc12d59decbcb236b9d1b954ffc8b50339233874cdcf98cae2b1c6502c64056cb621d9c94797aefd2'
del state,copy
data=bytes((i*17+11)&255 for i in range(111))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='b5a0b3d025c3a07ea2841d52295d77ed0b200e3f7e0c437a517af718cb061fbca8279e287d7fa2ec6336af3a437c6155'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='020495e1bc68b0e98ce6d00ae37715c12bc37c6756d5b218b2c2c2b05db817f5e9cede8c9ac23b18099590fc74d15220'
assert copy.hexdigest()=='b5a0b3d025c3a07ea2841d52295d77ed0b200e3f7e0c437a517af718cb061fbca8279e287d7fa2ec6336af3a437c6155'
del state,copy
data=bytes((i*17+11)&255 for i in range(112))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='728a7df4c19b63549e5ffde3af488d4d3ecc7783a843d552ef354a938e49bd31ed6fb0569c8fdb222f69bcad52b6a21b'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='1a870b309a291f798b4bc25a43c01d624d740f51f59956c5edda314eb99b15e27150e13766550486fbabc1e242dc37a0'
assert copy.hexdigest()=='728a7df4c19b63549e5ffde3af488d4d3ecc7783a843d552ef354a938e49bd31ed6fb0569c8fdb222f69bcad52b6a21b'
del state,copy
data=bytes((i*17+11)&255 for i in range(127))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='d3216c69601aa89c3f347df53f83d262ddf2f519446569c4b85c3247b372f8ef52352c879b4c086a2b1c9bb91f9ca294'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='6853307c28852279453c558f811b32b05cea1383c2630ceb9ce6bfc234b493a3ca0f2ef5b89c7e5f14db4c986980dd0c'
assert copy.hexdigest()=='d3216c69601aa89c3f347df53f83d262ddf2f519446569c4b85c3247b372f8ef52352c879b4c086a2b1c9bb91f9ca294'
del state,copy
data=bytes((i*17+11)&255 for i in range(128))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='bac8ee73162e31ee852f0a2220f175d8ee4622bb91a828ae42ea28e4746e8ae9a86b9946ee89fde2d6e650d415fb8c09'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='152e87263ba82c22dd26f9a2bc2a82c436bff661b694600175af9d164265a639cdc4f2c4b2470b330da81c0a9885d0ba'
assert copy.hexdigest()=='bac8ee73162e31ee852f0a2220f175d8ee4622bb91a828ae42ea28e4746e8ae9a86b9946ee89fde2d6e650d415fb8c09'
del state,copy
data=bytes((i*17+11)&255 for i in range(129))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='0d23bc3c172b61b0aeac6ddcc3e51d02f3f135243efa8071d6d43960b441c30f60229c9722ba7451b6f3c12bc9942c50'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='19de5cc884365ba31f714368c46fdcfacf6af2b8d0f9d8415870e9b5f87dabccede0ba7d83150d9a06287449b9a1128a'
assert copy.hexdigest()=='0d23bc3c172b61b0aeac6ddcc3e51d02f3f135243efa8071d6d43960b441c30f60229c9722ba7451b6f3c12bc9942c50'
del state,copy
data=bytes((i*17+11)&255 for i in range(1024))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='039b8c60b664f49af6d451d57d1d43968104eb9d7e1e14c19aa3c8d899528eac8d318a0a58961afb27879a7af113b7f8'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='0270f79af11c3f2992549318b687305322489ee4cbb87c6c4a1e13dd15fbe59148e9f6d6c19d63cca8e41bf1da12095a'
assert copy.hexdigest()=='039b8c60b664f49af6d451d57d1d43968104eb9d7e1e14c19aa3c8d899528eac8d318a0a58961afb27879a7af113b7f8'
del state,copy
key=b'public key'
msg=b'public message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='b9b4247f0890f7a80f1814e9b227b9536a88a6980cdd6a53d418f776d3df83019f2f3174a2b2240127dcf5abae0aa089'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='b9b4247f0890f7a80f1814e9b227b9536a88a6980cdd6a53d418f776d3df83019f2f3174a2b2240127dcf5abae0aa089'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'
msg=b'Hi There'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='afd03944d84895626b0825f4ab46907f15f9dadbe4101ec682aa034c7cebc59cfaea9ea9076ede7f4af152e8b2fa9cb6'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='afd03944d84895626b0825f4ab46907f15f9dadbe4101ec682aa034c7cebc59cfaea9ea9076ede7f4af152e8b2fa9cb6'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
msg=b'public long-key message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='c006f83d7833c4170e6187fa599597b2f3f42bcc3869711605481c2ad1046caa2eb9e75f3545c61412bedbaefb2b79ca'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='c006f83d7833c4170e6187fa599597b2f3f42bcc3869711605481c2ad1046caa2eb9e75f3545c61412bedbaefb2b79ca'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b''
msg=b''
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='6c1f2ee938fad2e24bd91298474382ca218c75db3d83e114b3d4367776d14d3551289e75e8209cd4b792302840234adc'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='6c1f2ee938fad2e24bd91298474382ca218c75db3d83e114b3d4367776d14d3551289e75e8209cd4b792302840234adc'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',1,1)).decode()=='63'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',2,48)).decode()=='768ab347c921bab8e75b867e7d0e1ff9ca3f5283e94e673a4d11da96b4ebac1ccdfc17fb77761667949d38cda7f6737f'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',65,49)).decode()=='7541039e85b3e4b7eb0d8a024d144bdc47f353f38a5ce29758d4d2cd10b2a13cc9dfd711bf11b6fa051fc32524462b7994'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',127,97)).decode()=='d70ad189322d162cdfe65da9343edd27f823cae357c0241bcc46278f0d45c624901fc59b6b99a737b09df2cb03e4ee3155dfe6310339454df9974cf9d438c8eef4330a7c1ebcc3a9ef00c23f5f9d7eb9080f8dfb74cfd29773236e46c812861af1'
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@HASH_ALGORITHM_PASS',name)
name='sha512'
assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==(64,128)
data=bytes((i*17+11)&255 for i in range(0))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='6a55ff599938be23142760d26476b58f175ceaf99dee4716a722d89b3ca670cc8441637132917f2fc8dd43164bc5c4318adf5c4a0d4d0cdfa654bf3a2f2ce963'
assert copy.hexdigest()=='cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'
del state,copy
data=bytes((i*17+11)&255 for i in range(1))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='527cff2b6fdfbc0f54fe092b17d6d8c7e22500242635fa56981e85a64da6ce8a12a3a66cf69fd48f588bcba9bad141b8e351a0cdd4925ae57289933eec1fc153'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='41dff7272ad7a1531e2494bd72bc3e75d3f87f7c45d2bc8ef1cb3495c81f961aa32de8c3b3c6826199c82fa1e57b64736617c2cc7a7738bd94a93a399554017a'
assert copy.hexdigest()=='527cff2b6fdfbc0f54fe092b17d6d8c7e22500242635fa56981e85a64da6ce8a12a3a66cf69fd48f588bcba9bad141b8e351a0cdd4925ae57289933eec1fc153'
del state,copy
data=bytes((i*17+11)&255 for i in range(55))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='24f26454cc643138441387eebcfd20b2f4dbde95fdaf8bcb6296b1f64d00671236433752f0089cb44b127e4eb8b1f179fb3b7220eac0e4aa9544f4615515ff8f'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='45af0cdf09ffdc5b60d6a57824c12ff59edd075c8fd4d153565cc96e7f6b0de893e13ae2ad1b8c46d1affdc283372011a6d2be5d5021742990024fc13e4246ac'
assert copy.hexdigest()=='24f26454cc643138441387eebcfd20b2f4dbde95fdaf8bcb6296b1f64d00671236433752f0089cb44b127e4eb8b1f179fb3b7220eac0e4aa9544f4615515ff8f'
del state,copy
data=bytes((i*17+11)&255 for i in range(56))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='fdb21bc913f62ade4d7a4134c44ddc0b6deaeeb3a04c5762d570320e2587a927398cd2d8a77512eb3c8a18fc89c5c6129e8e755967e3c3d35d4d6b87b98c7381'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='2dbbca5c6b3b2785adff637f88674cfdf29fd7351fb5973f7d60b85c1d9145049d52e9ee65d6f9f5079da31d6feace27debca7782ff4873e473a5bd628e4f5bf'
assert copy.hexdigest()=='fdb21bc913f62ade4d7a4134c44ddc0b6deaeeb3a04c5762d570320e2587a927398cd2d8a77512eb3c8a18fc89c5c6129e8e755967e3c3d35d4d6b87b98c7381'
del state,copy
data=bytes((i*17+11)&255 for i in range(63))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='196e3eb5c9586aac47a6fa0593e0070cf1c2ea4422a034578eaa13f2c6fe643229b941e201ab7a062bbd6682a626fa8d611eaeb862cf1e068e233fa9df4b6bc8'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='6734fbce47f7e04a4b287b2300e079dfcdcfe4a8dbf02251937745814502108e31435e0044a111074656ac538d39d0e053aae2c76773cef487b125149d2d1470'
assert copy.hexdigest()=='196e3eb5c9586aac47a6fa0593e0070cf1c2ea4422a034578eaa13f2c6fe643229b941e201ab7a062bbd6682a626fa8d611eaeb862cf1e068e233fa9df4b6bc8'
del state,copy
data=bytes((i*17+11)&255 for i in range(64))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='4e3049da4cb0ba12241f72f674f97a43bdd31ba123ff089514f9de1063ff304f9ecc33311a5e27c72320cc84115b2962193df2d9ee609f0af8f7ab7f0d2b121e'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='943c6aed9470c5163540dda80606126f9020ae3f41a54960185e42eebf0b90d6e3ac9207b67d5c88792d2002289ca574e45c6db9fdd0dd95d4207dbe29b8a850'
assert copy.hexdigest()=='4e3049da4cb0ba12241f72f674f97a43bdd31ba123ff089514f9de1063ff304f9ecc33311a5e27c72320cc84115b2962193df2d9ee609f0af8f7ab7f0d2b121e'
del state,copy
data=bytes((i*17+11)&255 for i in range(65))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='fc085d7ae9cdc7563d587a11d5a7e2cc999974994f169cca4c859ad47bebe3efd77816965b7ee89e308aa0fad687d99de3ff6f217b7e564a15b6373d2de20b98'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='341e774395ed19b6a04a46f20c6ee09332e753f45826bef97bb80542003b29f0cd0f120abb5af0547d8815ee516387102ee61de42f83e4d6155e6f32e83017b6'
assert copy.hexdigest()=='fc085d7ae9cdc7563d587a11d5a7e2cc999974994f169cca4c859ad47bebe3efd77816965b7ee89e308aa0fad687d99de3ff6f217b7e564a15b6373d2de20b98'
del state,copy
data=bytes((i*17+11)&255 for i in range(111))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a52de7197618c7f13ac4add5a357f67925f53a9969e55100b1ac1aafdd602fa3d524ac050c99d8e54915fe90200aa7c68f6943efe9c88e880efc95265fdb3f15'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='3e1b89ff2fe057288a88a25040166f1a69e84b96f4194b70031d07e52d8443f3bcb5ead1ce1a6909527715f5dd30dda7293f4a9e91812b4f51be1fb7e9afb4c6'
assert copy.hexdigest()=='a52de7197618c7f13ac4add5a357f67925f53a9969e55100b1ac1aafdd602fa3d524ac050c99d8e54915fe90200aa7c68f6943efe9c88e880efc95265fdb3f15'
del state,copy
data=bytes((i*17+11)&255 for i in range(112))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='19ca0398b7c606261ab3bf44457b7c5f50c20544152d60d16198100708dcd510d606dc29dd93ce770a724aee0707e3bfd8d4b46703e80f43c9df6f84a9b68048'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='5b6c888f8c2ee714883439aaba03c1f8e3d56126b0d96198f9589867212b132307514dc8028eddd5678332a7e1e02b9bcad7218a1b4451702ffdece8046c5aaa'
assert copy.hexdigest()=='19ca0398b7c606261ab3bf44457b7c5f50c20544152d60d16198100708dcd510d606dc29dd93ce770a724aee0707e3bfd8d4b46703e80f43c9df6f84a9b68048'
del state,copy
data=bytes((i*17+11)&255 for i in range(127))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='7a7267d58d09cf47b7653b8e1212c325f10dcf8107b3e2415d0c1d45d22e4af951d2b92f1ece358504e0f58c68a2040ed1e9c7fa843c278913b93edfdf958d7d'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='2e308ffcc614d6fb8f71686a10a569e466fb6b83b444a7ef37543f82c94b18f047d83e590fd9ba9fcce6f9436273b9ca0530c7f349f725b5930570f1870ff1a5'
assert copy.hexdigest()=='7a7267d58d09cf47b7653b8e1212c325f10dcf8107b3e2415d0c1d45d22e4af951d2b92f1ece358504e0f58c68a2040ed1e9c7fa843c278913b93edfdf958d7d'
del state,copy
data=bytes((i*17+11)&255 for i in range(128))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='c087ccc531bf8247a6863baa2a4a79629857780bb3af887d86b62a5e3e2aeeedcd54e2b47ac245a4ace397823b8c52a615c59d5959a7b6805eb2a231f8a1d3f1'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='58ec68d41cb76b680f257939f06d3883dd503d6cab62e87fbfb71a6ec9be53dabe189aafaaf286022525ea8d60572386d3d27df7e30b1417c78aa0ffefc982ea'
assert copy.hexdigest()=='c087ccc531bf8247a6863baa2a4a79629857780bb3af887d86b62a5e3e2aeeedcd54e2b47ac245a4ace397823b8c52a615c59d5959a7b6805eb2a231f8a1d3f1'
del state,copy
data=bytes((i*17+11)&255 for i in range(129))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e9fd8766d377cbc11c8b6499d087f970fd0a8da2d6f6a236601a71f22911fb516b93fefe6125cebaa973a1198ce051b96c1b1c6f9f00b22f5289fe330af3daaf'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='04ac8e2b1dd22a4491f8d3ce70f08f0d655bb830b54db5e56eaaa93084cce48cbb0823cea133ceafec43c995d8e306a56434d8db7a1875e83929c037df72f9e2'
assert copy.hexdigest()=='e9fd8766d377cbc11c8b6499d087f970fd0a8da2d6f6a236601a71f22911fb516b93fefe6125cebaa973a1198ce051b96c1b1c6f9f00b22f5289fe330af3daaf'
del state,copy
data=bytes((i*17+11)&255 for i in range(1024))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='c789b7414a3ad1297c7fe8f1568f11a251010e9a360c0f8214414103e2c37d4f672795602126630cf71a14b98fad276d02634102bbfc875242b55b5faada14ed'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='96e720142d641a4cae76357f12393ec36dbf671a15727cf94eb464530c14430cfab05423e4e1c234a9bc254b1c11e06124a1188d928b9589112a01455fdc05e0'
assert copy.hexdigest()=='c789b7414a3ad1297c7fe8f1568f11a251010e9a360c0f8214414103e2c37d4f672795602126630cf71a14b98fad276d02634102bbfc875242b55b5faada14ed'
del state,copy
key=b'public key'
msg=b'public message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='f4ac8cc7c458e8520d5007b8d705e14024062d7ade2f7bed10e35d72ad1ca73f0dfc5ebd864fa184b3cc53509e392fd2e19b03f62f5d9960eb10a087659c7cbf'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='f4ac8cc7c458e8520d5007b8d705e14024062d7ade2f7bed10e35d72ad1ca73f0dfc5ebd864fa184b3cc53509e392fd2e19b03f62f5d9960eb10a087659c7cbf'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'
msg=b'Hi There'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='87aa7cdea5ef619d4ff0b4241a1d6cb02379f4e2ce4ec2787ad0b30545e17cdedaa833b7d6b8a702038b274eaea3f4e4be9d914eeb61f1702e696c203a126854'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='87aa7cdea5ef619d4ff0b4241a1d6cb02379f4e2ce4ec2787ad0b30545e17cdedaa833b7d6b8a702038b274eaea3f4e4be9d914eeb61f1702e696c203a126854'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
msg=b'public long-key message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='dfa36b0ab3d3601347010f00fbc57c23531be068081cfd696a069f9d6b1b3deb22adff3975d05276ae037cab97abd87c95816a8d131b003895020fd4447d4961'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='dfa36b0ab3d3601347010f00fbc57c23531be068081cfd696a069f9d6b1b3deb22adff3975d05276ae037cab97abd87c95816a8d131b003895020fd4447d4961'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b''
msg=b''
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='b936cee86c9f87aa5d3c6f2e84cb5a4239a5fe50480a6ec66b70ab5b1f4ac6730c6c515421b327ec1d69402e53dfb49ad7381eb067b338fd7b0cb22247225d47'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='b936cee86c9f87aa5d3c6f2e84cb5a4239a5fe50480a6ec66b70ab5b1f4ac6730c6c515421b327ec1d69402e53dfb49ad7381eb067b338fd7b0cb22247225d47'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',1,1)).decode()=='53'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',2,64)).decode()=='6f2f484ded363329dd593fe295aa0af724bba0733e4ec6e661a9a198f547ae2ee2134b74794e94a9afe98a432678d37a99c6ebc9863a8b80522c28a8b4dd27d3'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',65,65)).decode()=='7df4d8c6666bffebaf44a9f8d3ff0ca2b5e63e81187fe92a2d3b1024b5b45c9e7b36c7e3c0577a5dc60f102bb95888ea797e48b7166a3040c0ebd067135f0bb029'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',127,129)).decode()=='ee785f0f58425fbe10c32e6bdb048c0362ceea3450293a7b2bd6d86c769031e862cd6c8eaa016b82e941e3cb17c8a032d38defbb1df583144bd7c42dd0ad2ed1d7b290d3a064cc949d0ac2a8883abc72ceea9221e1d2d0ac448a348af272d9c86ee6d077d090fea39c711a7c785896ac16bfe4fa3e449286f893eb80b0fee7723e'
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@HASH_ALGORITHM_PASS',name)
name='sha1'
assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==(20,64)
data=bytes((i*17+11)&255 for i in range(0))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='da39a3ee5e6b4b0d3255bfef95601890afd80709'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='91c3d164eb4ca589bc6c36684c3f167984290056'
assert copy.hexdigest()=='da39a3ee5e6b4b0d3255bfef95601890afd80709'
del state,copy
data=bytes((i*17+11)&255 for i in range(1))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='067d5096f219c64b53bb1c7d5e3754285b565a47'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='12082fc7a011728801d21e8563c9115de31807eb'
assert copy.hexdigest()=='067d5096f219c64b53bb1c7d5e3754285b565a47'
del state,copy
data=bytes((i*17+11)&255 for i in range(55))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e33b5fe821e8bee6a1a34f44fe0857fe8aaaeaa0'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='14cd9e824b7774909f7d28edab4ff42a487feb43'
assert copy.hexdigest()=='e33b5fe821e8bee6a1a34f44fe0857fe8aaaeaa0'
del state,copy
data=bytes((i*17+11)&255 for i in range(56))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='4064ac9f344e3607deee0b0628f596dbb4d30bce'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='d9bfb15b97b32397a64385ce614055a446697326'
assert copy.hexdigest()=='4064ac9f344e3607deee0b0628f596dbb4d30bce'
del state,copy
data=bytes((i*17+11)&255 for i in range(63))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a94b03ee2fc2c1da8904d8e5fd0eac9b8d432c3a'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='335c96d1ad3a49989afadc35fff8d47547c84d2b'
assert copy.hexdigest()=='a94b03ee2fc2c1da8904d8e5fd0eac9b8d432c3a'
del state,copy
data=bytes((i*17+11)&255 for i in range(64))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='f41dc3f7ad3638ed96d68bb158155139845c8171'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='54062b441714fda5e68959dc13f98f4944346cd7'
assert copy.hexdigest()=='f41dc3f7ad3638ed96d68bb158155139845c8171'
del state,copy
data=bytes((i*17+11)&255 for i in range(65))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='eec86c77395b30bbb7339692538bac577ccea8a0'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='32ef686e45e9abe3df1db1aa0a3feeb32549bca4'
assert copy.hexdigest()=='eec86c77395b30bbb7339692538bac577ccea8a0'
del state,copy
data=bytes((i*17+11)&255 for i in range(111))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e5029adc953a65025b6788c11be9983f17441663'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='be15e51f0983916a53e48578e8e36963b8922995'
assert copy.hexdigest()=='e5029adc953a65025b6788c11be9983f17441663'
del state,copy
data=bytes((i*17+11)&255 for i in range(112))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='1ddcda3742b5c7c6e88d2ee07e4587173fc95e3e'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='76debc44308d07e02739357f2107c3f1bfd71972'
assert copy.hexdigest()=='1ddcda3742b5c7c6e88d2ee07e4587173fc95e3e'
del state,copy
data=bytes((i*17+11)&255 for i in range(127))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='1562be7d8a8621b21eb8b6e5e43db847a65afb55'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='1a0d33c8cc0a6350c725be9c49228f0a0df6fdd5'
assert copy.hexdigest()=='1562be7d8a8621b21eb8b6e5e43db847a65afb55'
del state,copy
data=bytes((i*17+11)&255 for i in range(128))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a037f4552f5491b53727b144851cb2db5486938d'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='b8ae72a8f406b27d0b46bd567490bcd84e78b296'
assert copy.hexdigest()=='a037f4552f5491b53727b144851cb2db5486938d'
del state,copy
data=bytes((i*17+11)&255 for i in range(129))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a7971909e82d97be63692a552f7f3b8b03c8848c'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='38c15098d991fd51894ab7dcd56a71998ea39564'
assert copy.hexdigest()=='a7971909e82d97be63692a552f7f3b8b03c8848c'
del state,copy
data=bytes((i*17+11)&255 for i in range(1024))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='ccaff9b331d0c09a0848f0c5ffbdb50602889ba7'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='00f074104aa628e3c100e1402590a51e5da4a8ba'
assert copy.hexdigest()=='ccaff9b331d0c09a0848f0c5ffbdb50602889ba7'
del state,copy
key=b'public key'
msg=b'public message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='dbf29ca3eae4dae1c26e0a834c40afcd3d488936'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='dbf29ca3eae4dae1c26e0a834c40afcd3d488936'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'
msg=b'Hi There'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='b617318655057264e28bc0b6fb378c8ef146be00'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='b617318655057264e28bc0b6fb378c8ef146be00'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
msg=b'public long-key message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='284427c84b414476c27ba044f643e8f44074225a'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='284427c84b414476c27ba044f643e8f44074225a'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b''
msg=b''
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='fbdb1d1b18aa6c08324b7d64b71fb76370690e1d'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='fbdb1d1b18aa6c08324b7d64b71fb76370690e1d'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',1,1)).decode()=='ed'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',2,20)).decode()=='4b56be8b71719007bad637aba505dbd0fd01ce18'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',65,21)).decode()=='b30df2702615b3a77fd41740b0a93164988714bbf8'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',127,41)).decode()=='ac58e327803b6e63598a7c820d6090d11af019371eb36be752675e7b08f22f2145b550eb5c9ac9a144'
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@HASH_ALGORITHM_PASS',name)
name='ripemd160'
assert (hashlib.new(name).digest_size,hashlib.new(name).block_size)==(20,64)
data=bytes((i*17+11)&255 for i in range(0))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='9c1185a5c5e9fc54612808977ee8f548b2258d31'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='e66745a7f7dc976a6b9a27a1b5cc456c79295f8e'
assert copy.hexdigest()=='9c1185a5c5e9fc54612808977ee8f548b2258d31'
del state,copy
data=bytes((i*17+11)&255 for i in range(1))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e257e7861ba1b82bdcff75ff2bb1613d83b797bd'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='ed0924ea329969ab44b911551c0d63f31159882f'
assert copy.hexdigest()=='e257e7861ba1b82bdcff75ff2bb1613d83b797bd'
del state,copy
data=bytes((i*17+11)&255 for i in range(55))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='f717b23b09971e9d379a24bf470658f63c50f775'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='10309e30ec19ce56abb13ae2a0796d428f991063'
assert copy.hexdigest()=='f717b23b09971e9d379a24bf470658f63c50f775'
del state,copy
data=bytes((i*17+11)&255 for i in range(56))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='e07504cdb2e0a11c13c64aea8c83d1d389e6b7f8'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='9a80a9d7e2bef2fade73a2d388ddbe5cea18c55e'
assert copy.hexdigest()=='e07504cdb2e0a11c13c64aea8c83d1d389e6b7f8'
del state,copy
data=bytes((i*17+11)&255 for i in range(63))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='9cac371e685acb3816a350787bae87e71fd0e0ef'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='204b1c465c6e1aeaefe5d4688bc98c76bf85d4c2'
assert copy.hexdigest()=='9cac371e685acb3816a350787bae87e71fd0e0ef'
del state,copy
data=bytes((i*17+11)&255 for i in range(64))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='b0fd3369b593401f08d7902318201fc8e29431ce'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='6626272ec818b1203f7b91daa134dab31fed05ca'
assert copy.hexdigest()=='b0fd3369b593401f08d7902318201fc8e29431ce'
del state,copy
data=bytes((i*17+11)&255 for i in range(65))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='ec928a8a7b43dfbf8508db5a78da892dd0f98b9a'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='303baa4e57cbd0cd61eb33a3223cc6fca21ee0df'
assert copy.hexdigest()=='ec928a8a7b43dfbf8508db5a78da892dd0f98b9a'
del state,copy
data=bytes((i*17+11)&255 for i in range(111))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='cac78abef9552f80da2bef723725f1d0760300a2'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='ff50a5493760ec85839fb74d434126cf12732763'
assert copy.hexdigest()=='cac78abef9552f80da2bef723725f1d0760300a2'
del state,copy
data=bytes((i*17+11)&255 for i in range(112))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='a5abd81c43a6ae12e0472476a24b9c1de9bfd7e0'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='7b7fcf86afd00f84abcd96890b0e18711dceba13'
assert copy.hexdigest()=='a5abd81c43a6ae12e0472476a24b9c1de9bfd7e0'
del state,copy
data=bytes((i*17+11)&255 for i in range(127))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='2d65c27628645e04fc65d04014e5ab05fe5ace8f'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='2429bb404f4be46f3967b259132345ec903ee20e'
assert copy.hexdigest()=='2d65c27628645e04fc65d04014e5ab05fe5ace8f'
del state,copy
data=bytes((i*17+11)&255 for i in range(128))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='8327e793f4e868278e4244fde5b2a551d215d291'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='ff6a724356bb6a5ee512c93f770b1017e67edda5'
assert copy.hexdigest()=='8327e793f4e868278e4244fde5b2a551d215d291'
del state,copy
data=bytes((i*17+11)&255 for i in range(129))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='2f692faee18572cd201b81c85a43570f5bc9cc38'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='6cf547627bab9d44da7db34425ccb85ebc8f1e05'
assert copy.hexdigest()=='2f692faee18572cd201b81c85a43570f5bc9cc38'
del state,copy
data=bytes((i*17+11)&255 for i in range(1024))
state=hashlib.new(name)
for offset in range(0,len(data),17):state.update(memoryview(data)[offset:offset+17])
assert state.hexdigest()=='ffe46b2ced7218b0cd3dccc2c70c3141caf8e3e9'
assert state.digest()==state.digest()
copy=state.copy()
state.update(b'public suffix')
assert state.hexdigest()=='c0acd93b750f9c3dcbc569c7c82feaa46b663e52'
assert copy.hexdigest()=='ffe46b2ced7218b0cd3dccc2c70c3141caf8e3e9'
del state,copy
key=b'public key'
msg=b'public message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='65a2d6dd700b4e11a15a03a91dc47612648e419c'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='65a2d6dd700b4e11a15a03a91dc47612648e419c'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'
msg=b'Hi There'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='24cb4bd67d20fc1a5d2ed7732dcc39377f0a5668'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='24cb4bd67d20fc1a5d2ed7732dcc39377f0a5668'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b'KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK'
msg=b'public long-key message'
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='99f40981f78ead908171c6ea8ab200b7886adc4d'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='99f40981f78ead908171c6ea8ab200b7886adc4d'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
key=b''
msg=b''
assert binascii.hexlify(hmac.digest(key,msg,name)).decode()=='44d86b658a3e7cbc1a2010848b53e35c917720ca'
state=hmac.new(key,msg[:3],name)
copy=state.copy()
state.update(msg[3:])
copy.update(msg[3:])
assert state.hexdigest()=='44d86b658a3e7cbc1a2010848b53e35c917720ca'
assert copy.digest()==state.digest()
assert state.digest()==state.digest()
assert state.name=='hmac-'+name
del state,copy
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',1,1)).decode()=='8b'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',2,20)).decode()=='addc38d03945005a69ace630da6d72f403512e77'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',65,21)).decode()=='b297dc3d3989319677d5ecc2fdcccca97f58d3530b'
assert binascii.hexlify(hashlib.pbkdf2_hmac(name,b'public password',b'public salt',127,41)).decode()=='8d397356f199d3daaa0c345db437c3f9b7c6410cba956b4f49a60c9039d218519e66fe0b24237b870c'
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@HASH_ALGORITHM_PASS',name)
start=time.ticks_ms()
value=hashlib.pbkdf2_hmac('sha1',b'password',b'salt',4096,20)
assert binascii.hexlify(value).decode()=='4b007901b765489abead49d926f721d065a429c1'
print('@@PBKDF2_VECTOR_MS','sha1',4096,(time.ticks_ms()-start)&0xffffffff)
start=time.ticks_ms()
value=hashlib.pbkdf2_hmac('sha1',b'pass\x00word',b'sa\x00lt',4096,16)
assert binascii.hexlify(value).decode()=='56fa6aa75548099dcc37d7f03425e0c3'
print('@@PBKDF2_VECTOR_MS','sha1',4096,(time.ticks_ms()-start)&0xffffffff)
start=time.ticks_ms()
value=hashlib.pbkdf2_hmac('sha512',b'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',b'mnemonicTREZOR',2048,64)
assert binascii.hexlify(value).decode()=='c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04'
print('@@PBKDF2_VECTOR_MS','sha512',2048,(time.ticks_ms()-start)&0xffffffff)
for name in hashlib.algorithms_available:
    assert hashlib.new(name,bytearray()).digest()==hashlib.new(name,b'').digest()
    state=hashlib.new(name)
    state.update(memoryview(bytearray()))
    assert state.digest()==hashlib.new(name,b'').digest()
assert hmac.digest(bytearray(),bytearray(),'sha256')==hmac.digest(b'',b'','sha256')
assert hashlib.pbkdf2_hmac('sha256',bytearray(),bytearray(),2)==hashlib.pbkdf2_hmac('sha256',b'',b'',2)
assert hmac.compare_digest(bytearray(),bytearray())
assert hmac.digest(b'key',b'message',hashlib.sha512)==hmac.digest(b'key',b'message','sha512')
assert hmac.compare_digest(b'public',b'public')
assert not hmac.compare_digest(b'public',b'Public')
assert not hmac.compare_digest(b'public',b'public extra')
assert hmac.compare_digest('public','public')
for a,b in [('é','é'),('public',b'public')]:
    try:hmac.compare_digest(a,b)
    except TypeError:pass
    else:raise AssertionError('invalid digest comparison accepted')
for value in ['text',123]:
    try:hashlib.sha256(value)
    except TypeError:pass
    else:raise AssertionError('invalid hash data accepted')
for rounds,length in [(0,32),(-1,32),(1,0),(1,4097),(1000001,32),(1000000,65)]:
    try:hashlib.pbkdf2_hmac('sha256',b'p',b's',rounds,length)
    except ValueError:pass
    else:raise AssertionError('invalid KDF work accepted')
state=hashlib.sha256(b'public')
state._state.__del__()
try:state.digest()
except ValueError:pass
else:raise AssertionError('cleared hash state reused')
del state
for i in range(300):
    state=hashlib.sha512(b'public')
    temporary=state.copy().digest()
del state,temporary
gc.collect()
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS native-hash-hmac-pbkdf2')
