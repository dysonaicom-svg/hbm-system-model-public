// ------------------------------------------------------------
// uvm.svh - Verilator-compatible UVM package stub
// Simplified for syntax checking with Verilator
// ------------------------------------------------------------
package uvm_pkg;

    // =============================================================
    // Constants and Enums
    // =============================================================
    typedef enum { UVM_NONE=0, UVM_LOW=100, UVM_MEDIUM=200, UVM_HIGH=300, UVM_FULL=400, UVM_DEBUG=500 } verbosity_t;
    typedef enum int { UVM_NO_HIER=0, UVM_HIER=1 } uvm_apprecy_t;
    typedef enum { UVM_OK=0, UVM_NOT_OK, UVM_ERR, UVM_WARNING, UVM_INFO } uvm_severity_e;
    typedef enum { UVM_HEX, UVM_DEC, UVM_BIN, UVM_OCT, UVM_UNSIGNED, UVM_STRING, UVM_TIME, UVM_NORADIX } uvm_radix_enum;

    const int UVM_ACTIVE = 1;
    const int UVM_PASSIVE = 0;

    // =============================================================
    // Phase Class
    // =============================================================
    class uvm_phase;
        string name;
        function new(string name); this.name = name; endfunction
    endclass

    // =============================================================
    // UVM Object Base Class
    // =============================================================
    class uvm_object;
        string name;
        function new(string name = ""); this.name = name; endfunction
        virtual function string get_name(); return name; endfunction
        virtual function string convert2string(); return name; endfunction
        virtual function void do_copy(uvm_object rhs); endfunction
        virtual function bit do_compare(uvm_object rhs); return 0; endfunction
        virtual function void do_print(); endfunction
        virtual function void print(); do_print(); endfunction
        virtual function void post_randomize(); endfunction
    endclass

    // =============================================================
    // UVM Printer
    // =============================================================
    class uvm_printer;
        int indent = 0;
    endclass

    // =============================================================
    // UVM Comparer
    // =============================================================
    class uvm_comparer;
        int unsigned max_errors = 50;
        int miss_match = 0;
    endclass

    // =============================================================
    // UVM Component Base Class
    // =============================================================
    class uvm_component extends uvm_object;
        uvm_component parent;
        uvm_phase phase;

        function new(string name, uvm_component parent);
            super.new(name);
            this.parent = parent;
        endfunction

        virtual function void build_phase(uvm_phase phase); endfunction
        virtual function void connect_phase(uvm_phase phase); endfunction
        virtual function void end_of_elaboration_phase(uvm_phase phase); endfunction
        virtual function void extract_phase(uvm_phase phase); endfunction
        virtual function void check_phase(uvm_phase phase); endfunction
        virtual function void report_phase(uvm_phase phase); endfunction

        function bit get_config_int(string field_name, inout bit value); return 0; endfunction
        function bit get_config_object(string field_name, inout uvm_object value); return 0; endfunction
    endclass

    // =============================================================
    // UVM Sequence Item
    // =============================================================
    class uvm_sequence_item extends uvm_object;
        int transaction_id = -1;

        function new(string name = ""); super.new(name); endfunction
        function void set_id(int id); transaction_id = id; endfunction
        function int get_id(); return transaction_id; endfunction
    endclass

    // =============================================================
    // UVM Sequencer
    // =============================================================
    class uvm_sequencer extends uvm_component;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Driver
    // =============================================================
    class uvm_driver extends uvm_component;
        uvm_sequence_item req;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Monitor
    // =============================================================
    class uvm_monitor extends uvm_component;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Sequence
    // =============================================================
    class uvm_sequence extends uvm_sequence_item;
        bit is_item = 0;
        function new(string name = ""); super.new(name); endfunction
        virtual task body(); endtask
        function void start_item(uvm_sequence_item item, int set_priority = -1); endfunction
        function void finish_item(uvm_sequence_item item); endfunction
    endclass

    // =============================================================
    // UVM Environment
    // =============================================================
    class uvm_env extends uvm_component;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Test
    // =============================================================
    class uvm_test extends uvm_env;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Agent
    // =============================================================
    class uvm_agent extends uvm_component;
        bit is_active = 1;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Scoreboard
    // =============================================================
    class uvm_scoreboard extends uvm_component;
        function new(string name, uvm_component parent); super.new(name, parent); endfunction
    endclass

    // =============================================================
    // UVM Analysis Port (simplified)
    // =============================================================
    class uvm_analysis_port;
        string port_name;
        function new(string name); this.port_name = name; endfunction
        function void write(uvm_sequence_item t); endfunction
        function void connect(uvm_component imp); endfunction
    endclass

    class uvm_analysis_export;
        string export_name;
        function new(string name); this.export_name = name; endfunction
        function void write(uvm_sequence_item t); endfunction
    endclass

    // =============================================================
    // UVM Config Database
    // =============================================================
    class uvm_config_db;
        static function bit get(uvm_component c, string inst_name, string field_name); return 0; endfunction
        static function void set(uvm_component c, string inst_name, string field_name, uvm_object value); endfunction
    endclass

    // =============================================================
    // UVM Objection
    // =============================================================
    class uvm_objection;
        static function void raise_objection(uvm_object obj, string description = ""); endfunction
        static function void drop_objection(uvm_object obj, string description = ""); endfunction
    endclass

    // =============================================================
    // Message Macros
    // =============================================================
    `define uvm_info(ID,MSG,VERBOSITY) \
        $display("[INFO %s] %s", ID, MSG);

    `define uvm_warning(ID,MSG) \
        $display("[WARN %s] %s", ID, MSG);

    `define uvm_error(ID,MSG) \
        $display("[ERROR %s] %s", ID, MSG);

    `define uvm_fatal(ID,MSG) \
        $display("[FATAL %s] %s", ID, MSG); $finish;

    // =============================================================
    // Field Macros
    // =============================================================
    `define uvm_field_utils(TYPE)
    `define uvm_field_object(ARG,FLAG)
    `define uvm_field_int(ARG,FLAG)
    `define uvm_field_string(ARG,FLAG)

    // =============================================================
    // Type Registration Macros
    // =============================================================
    `define uvm_component_utils(TYPE)
    `define uvm_object_utils(TYPE)
    `define uvm_component_param_utils(TYPE)
    `define uvm_object_param_utils(TYPE)
    `define uvm_sequence_utils(TYPE)

    // =============================================================
    // Sequence Item Macros
    // =============================================================
    `define uvm_do(req)
    `define uvm_rand_send(req)
    `define uvm_create(req)
    `define uvm_send(req)
    `define uvm_send_rand(req)

    // =============================================================
    // Declaration of run_test
    // =============================================================
    function void run_test(string test_name = "");
        $display("Running test: %s", test_name);
    endfunction

endpackage : uvm_pkg