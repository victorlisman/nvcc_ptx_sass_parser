# ir.py

WRITE_KERNEL_IR = [
    {"op": "ld.param.u64", "dst": "rd1", "src": "out"},
    {"op": "cvta.to.global.u64", "dst": "rd2", "src": "rd1"},
    {"op": "mov.u32", "dst": "r1", "src": "ctaid.x"},
    {"op": "mov.u32", "dst": "r2", "src": "ntid.x"},
    {"op": "mov.u32", "dst": "r3", "src": "tid.x"},
    {"op": "mad.lo.s32", "dst": "r4", "src1": "r1", "src2": "r2", "src3": "r3"},
    {"op": "mul.wide.s32", "dst": "rd3", "src1": "r4", "src2": 4},
    {"op": "add.s64", "dst": "rd4", "src1": "rd2", "src2": "rd3"},
    {"op": "mov.u32", "dst": "r5", "src": 1065353216},
    {"op": "st.global.u32", "addr": "rd4", "val": "r5"}
]