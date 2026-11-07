// WebGPU rejects resizable/growable backing stores, including Wasm heap views.
// This also runs in pthread workers when an existing player is served.
(function () {
  if (typeof GPUQueue === 'undefined') return;
  const proto = GPUQueue.prototype;
  const marker = Symbol.for('cyberarcade.ps2.fixedUpload');
  if (proto[marker]) return;
  const writeBuffer = proto.writeBuffer;
  let staging = new Uint8Array(0);
  Object.defineProperty(proto, 'writeBuffer', {
    configurable: true, writable: true,
    value: function (target, targetOffset, data, dataOffset, size) {
      const view = ArrayBuffer.isView(data);
      const backing = view ? data.buffer : data;
      if (!backing || (!backing.resizable && !backing.growable)) {
        return writeBuffer.apply(this, arguments);
      }
      const unit = view ? (data.BYTES_PER_ELEMENT || 1) : 1;
      const start = (dataOffset === undefined ? 0 : dataOffset) * unit;
      const available = data.byteLength;
      const length = size === undefined ? available - start : size * unit;
      // Leave invalid offsets and sizes to WebGPU's normal validation.
      if (!Number.isSafeInteger(start) || !Number.isSafeInteger(length) ||
          start < 0 || length < 0 || start + length > available) {
        return writeBuffer.apply(this, arguments);
      }
      if (staging.byteLength < length) {
        staging = new Uint8Array(Math.max(length, staging.byteLength * 2, 4096));
      }
      staging.set(new Uint8Array(backing, (view ? data.byteOffset : 0) + start, length));
      // writeBuffer snapshots these bytes synchronously, so staging is reusable.
      return writeBuffer.call(this, target, targetOffset, staging, 0, length);
    }
  });
  Object.defineProperty(proto, marker, {value: true});
})();

// Dynamic offsets are also passed from the Wasm heap by emdawnwebgpu.
(function () {
  const marker = Symbol.for('cyberarcade.ps2.fixedBindOffsets');
  for (const name of ['GPUComputePassEncoder', 'GPURenderPassEncoder', 'GPURenderBundleEncoder']) {
    const proto = globalThis[name]?.prototype;
    if (!proto || proto[marker] || typeof proto.setBindGroup !== 'function') continue;
    const original = proto.setBindGroup;
    Object.defineProperty(proto, 'setBindGroup', {
      configurable: true, writable: true,
      value: function (index, group, offsets, start, length) {
        if (!ArrayBuffer.isView(offsets) ||
            (!offsets.buffer.resizable && !offsets.buffer.growable)) {
          return original.apply(this, arguments);
        }
        // Only handle the typed-array overload; native validation handles invalid calls.
        if (!(offsets instanceof Uint32Array) || arguments.length < 5 ||
            !Number.isSafeInteger(start) || !Number.isSafeInteger(length) ||
            start < 0 || length < 0 || start + length > offsets.length) {
          return original.apply(this, arguments);
        }
        const fixed = new Uint32Array(length);
        fixed.set(offsets.subarray(start, start + length));
        return original.call(this, index, group, fixed, 0, length);
      }
    });
    Object.defineProperty(proto, marker, {value: true});
  }
})();
