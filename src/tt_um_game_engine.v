module tt_um_game_engine (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out
);

    reg [3:0] player;
    reg [3:0] obstacle;
    reg [3:0] score;

    always @(posedge clk) begin
        if (!rst_n) begin
            player   <= 4'd0;
            obstacle <= 4'd15;
            score    <= 4'd0;
        end else begin
            // Bouton joueur
            if (ui_in[0])
                player <= player + 1;

            // Obstacle automatique
            obstacle <= obstacle - 1;

            // Collision
            if (player == obstacle) begin
                score    <= score + 1;
                obstacle <= 4'd15;
            end
        end
    end

    assign uo_out = {score, player};

endmodule
