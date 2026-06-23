// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VHBM_CONTROLLER_TB_SIMPLE__SYMS_H_
#define VERILATED_VHBM_CONTROLLER_TB_SIMPLE__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vhbm_controller_tb_simple.h"

// INCLUDE MODULE CLASSES
#include "Vhbm_controller_tb_simple___024root.h"
#include "Vhbm_controller_tb_simple___024unit.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES)Vhbm_controller_tb_simple__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vhbm_controller_tb_simple* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vhbm_controller_tb_simple___024root TOP;

    // CONSTRUCTORS
    Vhbm_controller_tb_simple__Syms(VerilatedContext* contextp, const char* namep, Vhbm_controller_tb_simple* modelp);
    ~Vhbm_controller_tb_simple__Syms();

    // METHODS
    const char* name() { return TOP.name(); }
};

#endif  // guard
