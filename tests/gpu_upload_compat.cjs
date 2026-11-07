// Reproduce the WebGPU backing-store restriction without a physical GPU.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../web/gpu_upload_compat.js'), 'utf8');
const calls = [];
class GPUQueue {
  writeBuffer(target, offset, data, start = 0, size) {
    const view = ArrayBuffer.isView(data), backing = view ? data.buffer : data;
    if (backing.resizable || backing.growable) throw new TypeError('GPUQueue.writeBuffer: resizable backing store');
    const unit = view ? (data.BYTES_PER_ELEMENT || 1) : 1;
    const length = size === undefined ? data.byteLength - start * unit : size * unit;
    calls.push({queue: this, target, offset, data,
      bytes: Array.from(new Uint8Array(backing, (view ? data.byteOffset : 0) + start * unit, length))});
  }
}
const scope = vm.createContext({GPUQueue, ArrayBuffer, Uint8Array, Symbol, Number, Math});
const queue = new GPUQueue(), buffer = {};
const resizable = new ArrayBuffer(32, {maxByteLength: 64});
new Uint8Array(resizable).set(Array.from({length: 32}, (_, i) => i));
assert.throws(() => queue.writeBuffer(buffer, 0, new Uint8Array(resizable)), /resizable/);
vm.runInContext(source, scope);
queue.writeBuffer(buffer, 4, new Uint32Array(resizable, 4, 5), 1, 2);
assert.deepEqual(calls.at(-1).bytes, [8,9,10,11,12,13,14,15]);
assert.equal(calls.at(-1).queue, queue); assert.equal(calls.at(-1).offset, 4);
queue.writeBuffer(buffer, 0, new DataView(resizable, 4, 12), 4, 4);
assert.deepEqual(calls.at(-1).bytes, [8,9,10,11]);
queue.writeBuffer(buffer, 0, resizable, 16, 4);
assert.deepEqual(calls.at(-1).bytes, [16,17,18,19]);
resizable.resize(48);
new Uint8Array(resizable, 32).fill(23);
queue.writeBuffer(buffer, 0, new Uint8Array(resizable, 32), 0, 4);
assert.deepEqual(calls.at(-1).bytes, [23,23,23,23]);
const shared = new SharedArrayBuffer(32, {maxByteLength: 64});
new Uint8Array(shared).fill(31);
queue.writeBuffer(buffer, 0, new Uint8Array(shared));
assert.equal(calls.at(-1).bytes.length, 32);
assert(calls.at(-1).bytes.every(x => x === 31));
shared.grow(64);
new Uint8Array(shared, 32).fill(42);
queue.writeBuffer(buffer, 0, new Uint32Array(shared), 8);
assert.deepEqual(calls.at(-1).bytes, Array(32).fill(42));
const fixed = new Uint8Array(4);
queue.writeBuffer(buffer, 0, fixed);
assert.equal(calls.at(-1).data, fixed, 'fixed buffers keep the zero-copy path');
queue.writeBuffer(buffer, 0, shared, 0, 0);
assert.deepEqual(calls.at(-1).bytes, []);
const wrapper = GPUQueue.prototype.writeBuffer;
vm.runInContext(source, scope);
assert.equal(wrapper, GPUQueue.prototype.writeBuffer, 'server prefix plus pre-js is idempotent');
vm.runInNewContext(source, {}); // Firefox/software contexts need no GPUQueue.
console.log('PASS: resizable and growable backing stores, typed-element offsets, DataView/ArrayBuffer, growth, zero size, fixed fast path and worker-safe installation');

const bindings=[];
class Encoder {
 setBindGroup(index,group,data,start,length) {
  if(data?.buffer?.resizable || data?.buffer?.growable) throw new TypeError('resizable offsets');
  bindings.push({self:this,index,group,data,start,length});
 }
}
for(const name of ['GPUComputePassEncoder','GPURenderPassEncoder','GPURenderBundleEncoder']) {
 scope[name]=class extends Encoder {};
}
scope.Uint32Array=Uint32Array;
vm.runInContext(source,scope);
for(const name of ['GPUComputePassEncoder','GPURenderPassEncoder','GPURenderBundleEncoder']) {
 const encoder=new scope[name]();
 for(const buffer of [resizable,shared]) {
  const offsets=new Uint32Array(buffer);offsets.set([256,512,768,1024]);
  encoder.setBindGroup(1,null,offsets,1,2);
  const call=bindings.at(-1);assert.equal(call.self,encoder);assert.equal(call.start,0);assert.equal(call.length,2);
  assert.deepEqual(Array.from(call.data),[512,768]);assert.equal(call.data.buffer.resizable,false);
  assert.throws(()=>encoder.setBindGroup(0,null,offsets,-1,1),/resizable/);
 }
 const fixed=new Uint32Array([256]);encoder.setBindGroup(0,null,fixed,0,1);assert.equal(bindings.at(-1).data,fixed);
 encoder.setBindGroup(0,null);assert.equal(bindings.at(-1).data,undefined);
 const before=scope[name].prototype.setBindGroup;vm.runInContext(source,scope);assert.equal(scope[name].prototype.setBindGroup,before);
}
console.log('PASS: dynamic offset slices on compute/render/bundle encoders, shared growth, native invalid-input handling and idempotence');
