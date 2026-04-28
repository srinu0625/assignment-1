using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class GTAGameManager : MonoBehaviour
{
    public static GTAGameManager Instance;
    
    [Header("Player References")]
    public Transform player;
    public Camera mainCamera;
    
    [Header("UI")]
    public Text weaponText;
    public Text healthText;
    public Text wantedLevelText;
    public Text vehicleText;
    
    [Header("Game Settings")]
    public int maxWantedLevel = 5;
    public float policeSpawnDistance = 50f;
    
    [System.NonSerialized] public int currentWantedLevel = 0;
    [System.NonSerialized] public bool isPaused = false;
    
    private PlayerController playerController;
    private List<EnemyAI> activeEnemies = new List<EnemyAI>();
    
    void Awake()
    {
        Instance = this;
        playerController = player.GetComponent<PlayerController>();
    }
    
    void Update()
    {
        UpdateUI();
        HandlePoliceSpawning();
        CheckPause();
    }
    
    void UpdateUI()
    {
        if (playerController != null)
        {
            healthText.text = "HEALTH: " + playerController.health;
            weaponText.text = "WEAPON: " + playerController.currentWeapon;
            
            string stars = "";
            for (int i = 0; i < currentWantedLevel; i++) stars += "★";
            wantedLevelText.text = "WANTED: " + stars;
            
            if (playerController.inVehicle)
                vehicleText.text = "PRESS F TO EXIT VEHICLE";
            else
                vehicleText.text = "PRESS F NEAR VEHICLE TO ENTER";
        }
    }
    
    void HandlePoliceSpawning()
    {
        // Simple police spawn logic based on wanted level
        if (currentWantedLevel > 0 && activeEnemies.Count < currentWantedLevel * 2)
        {
            if (Random.Range(0, 100) < 1) // 1% chance per frame
            {
                SpawnPolice();
            }
        }
    }
    
    void SpawnPolice()
    {
        Vector3 spawnPos = player.position + Random.insideUnitSphere * policeSpawnDistance;
        spawnPos.y = player.position.y;
        
        GameObject police = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        police.transform.position = spawnPos;
        police.name = "Police";
        police.tag = "Enemy";
        
        EnemyAI enemy = police.AddComponent<EnemyAI>();
        enemy.target = player;
        activeEnemies.Add(enemy);
        
        // Add gun
        GameObject gun = GameObject.CreatePrimitive(PrimitiveType.Cube);
        gun.transform.SetParent(police.transform);
        gun.transform.localPosition = new Vector3(0.5f, 0, 0.5f);
        gun.transform.localScale = Vector3.one * 0.2f;
    }
    
    public void AddWantedLevel(int amount)
    {
        currentWantedLevel = Mathf.Min(currentWantedLevel + amount, maxWantedLevel);
    }
    
    public void ReduceWantedLevel(int amount)
    {
        currentWantedLevel = Mathf.Max(currentWantedLevel - amount, 0);
    }
    
    void CheckPause()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            isPaused = !isPaused;
            Time.timeScale = isPaused ? 0 : 1;
        }
    }
}
