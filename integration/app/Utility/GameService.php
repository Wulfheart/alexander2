<?php

namespace App\Utility;

use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class GameService
{
    protected string $basePath;
    public PendingRequest $client;
    public int $currentIndex = 0;
    public array $currentData = [];
    public array $previousData = [];
    public array $orders = [];

    public function __construct(string $base)
    {
        $this->client = Http::baseUrl(env('API_BASE_URL'));
        $currentTime = str_replace(':', '-', now()->toDateTimeLocalString());
        $this->basePath = $base . '/' . $currentTime;
    }

    public function saveImgFiles()
    {

        $baseAdjudicatedPath = "{$this->basePath}/{$this->currentIndex}_{$this->currentData['phase_short']}_0_adjudicated";
        $svgAdjudicated = $this->currentData['svg_adjudicated'];
        Storage::put("$baseAdjudicatedPath.svg", $svgAdjudicated);



        // Save game_encoded
        $baseAdjudicatedPath = "{$this->basePath}/state/{$this->currentIndex}_{$this->currentData['phase_short']}";
        $data = $this->currentData['current_state_encoded'];
        Storage::put("$baseAdjudicatedPath.txt", $data);

        if (!empty($this->previousData)) {
            $previousIndex = $this->currentIndex - 1;
            $baseWithOrdersPath = "{$this->basePath}/{$previousIndex}_{$this->previousData['phase_short']}_1_with_orders";
            $svgWithOrders = $this->currentData['svg_with_orders'];
            Storage::put("$baseWithOrdersPath.svg", $svgWithOrders);
        }
    }

    public function initGame()
    {
        $response = $this->client->get('/adjudicate/standard');
        $this->currentData = $response->json();
    }

    public function adjudicate()
    {
        $response = $this->client->post('adjudicate', [
            'previous_state_encoded' => $this->currentData['current_state_encoded'],
            'orders' => (object)$this->orders,
            'scs_to_win' => 18,
        ]);
        $this->previousData = $this->currentData;

        $this->currentData = $response->json();
        $this->currentIndex++;
        $this->orders = [];
    }

    public function isCompleted(): bool
    {
        return ($this->currentData['phase_short'] ?? '') == "COMPLETED";
    }


    public function assignRandomOrders(string $power)
    {
        foreach ($this->currentData['possible_orders'][$power] as $payload) {
            if(count($payload) > 0){
                $this->orders[$power][] = $payload[array_rand($payload)];
            }
        }
    }

    public function assignDumbbotOrders(string $power)
    {
        $response = $this->client->post('dumbbot', [
            'current_state_encoded' => $this->currentData['current_state_encoded'],
            'power' => Str::of($power)->upper(),
        ]);

        $this->orders[$power] = $response->json();


    }
}