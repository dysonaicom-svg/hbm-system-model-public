// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vhbm_controller_tb_simple.h for the primary calling header

#ifndef VERILATED_VHBM_CONTROLLER_TB_SIMPLE___024UNIT_H_
#define VERILATED_VHBM_CONTROLLER_TB_SIMPLE___024UNIT_H_  // guard

#include "verilated.h"


class Vhbm_controller_tb_simple__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vhbm_controller_tb_simple___024unit final : public VerilatedModule {
  public:

    // INTERNAL VARIABLES
    Vhbm_controller_tb_simple__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vhbm_controller_tb_simple___024unit(Vhbm_controller_tb_simple__Syms* symsp, const char* v__name);
    ~Vhbm_controller_tb_simple___024unit();
    VL_UNCOPYABLE(Vhbm_controller_tb_simple___024unit);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
